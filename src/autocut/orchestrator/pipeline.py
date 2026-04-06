from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import get_asr_connector, get_hooks_connector, get_render_connector
from autocut.io.manifest import load_manifest
from autocut.io.validation import ensure_valid_manifest
from autocut.models import ScenePlan, TranscriptSegment
from autocut.render.scene_plan import plan_scenes


def _slice_scene_plan(scene_plan: ScenePlan, from_scene: int | None, to_scene: int | None) -> ScenePlan:
    if from_scene is None and to_scene is None:
        return scene_plan

    start = 0 if from_scene is None else max(0, from_scene)
    end = len(scene_plan.scenes) if to_scene is None else min(len(scene_plan.scenes), to_scene + 1)
    return ScenePlan(episode_id=scene_plan.episode_id, scenes=scene_plan.scenes[start:end])


def _write_overrides_template(scene_plan, artifacts_dir: Path) -> None:
    template = {
        "overrides": [
            {
                "scene_index": i,
                "headline": scene.headline,
                "visual_ref": Path(scene.visual_ref).name,
                "start_s": round(scene.start_s, 2),
                "end_s": round(scene.end_s, 2),
                "mascot_action": scene.mascot_action,
            }
            for i, scene in enumerate(scene_plan.scenes)
        ]
    }
    (artifacts_dir / "overrides_template.json").write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_cached_transcript(cache_path: Path, audio_path: Path) -> list[TranscriptSegment] | None:
    if not cache_path.exists() or not audio_path.exists():
        return None

    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    if raw.get("audio_mtime") != audio_path.stat().st_mtime:
        return None

    return [
        TranscriptSegment(start_s=float(s["start_s"]), end_s=float(s["end_s"]), text=s["text"])
        for s in raw.get("segments", [])
    ]


def _save_cached_transcript(cache_path: Path, audio_path: Path, transcript: list[TranscriptSegment]) -> None:
    payload = {
        "audio_mtime": audio_path.stat().st_mtime if audio_path.exists() else None,
        "segments": [
            {"start_s": s.start_s, "end_s": s.end_s, "text": s.text}
            for s in transcript
        ],
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _probe_media(path: Path) -> dict[str, float | int | None]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=width,height:format=duration",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        stream0 = streams[0] if streams else {}
        return {
            "duration": float(data.get("format", {}).get("duration", 0.0) or 0.0),
            "width": int(stream0.get("width", 0) or 0),
            "height": int(stream0.get("height", 0) or 0),
        }
    except Exception:
        return {"duration": None, "width": None, "height": None}


def _probe_loudness(path: Path) -> dict[str, float | None]:
    if not path.exists() or path.stat().st_size == 0:
        return {"max_volume": None, "mean_volume": None}
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        stderr = result.stderr
        max_m = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", stderr)
        mean_m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", stderr)
        return {
            "max_volume": float(max_m.group(1)) if max_m else None,
            "mean_volume": float(mean_m.group(1)) if mean_m else None,
        }
    except Exception:
        return {"max_volume": None, "mean_volume": None}


def _run_qc(artifacts_dir: Path, voice_path: Path) -> None:
    issues: list[str] = []

    final_path = artifacts_dir / "final.mp4"
    render_outputs = artifacts_dir / "render_outputs.json"

    if not final_path.exists():
        issues.append("final.mp4 is missing")
    elif final_path.stat().st_size == 0:
        issues.append("final.mp4 is empty")

    if not render_outputs.exists():
        issues.append("render_outputs.json is missing")

    if final_path.exists() and final_path.stat().st_size > 0:
        video_meta = _probe_media(final_path)
        if video_meta["width"] and video_meta["height"]:
            if int(video_meta["width"]) < 720 or int(video_meta["height"]) < 1280:
                issues.append("final.mp4 resolution is below 720x1280")

        if voice_path.exists() and voice_path.stat().st_size > 0:
            voice_meta = _probe_media(voice_path)
            vd = video_meta.get("duration")
            ad = voice_meta.get("duration")
            if isinstance(vd, float) and isinstance(ad, float) and vd > 0 and ad > 0 and abs(vd - ad) > 3.0:
                issues.append("video/audio duration mismatch > 3s")

            loud = _probe_loudness(voice_path)
            if isinstance(loud.get("max_volume"), float) and loud["max_volume"] > -1.0:
                issues.append("voice track may be clipping (max_volume > -1 dB)")
            if isinstance(loud.get("mean_volume"), float) and loud["mean_volume"] < -35.0:
                issues.append("voice track too quiet (mean_volume < -35 dB)")

    status = "ok" if not issues else "warning"
    (artifacts_dir / "qc_report.json").write_text(
        json.dumps({"status": status, "issues": issues}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_pipeline(
    repo_root: Path,
    episode_id: str,
    settings: ProviderSettings | None = None,
    from_scene: int | None = None,
    to_scene: int | None = None,
) -> None:
    settings = settings or ProviderSettings.from_env()
    manifest = load_manifest(repo_root, episode_id)
    ensure_valid_manifest(manifest)

    asr = get_asr_connector(settings)
    hooks = get_hooks_connector(settings)
    renderer = get_render_connector(settings)

    artifacts_dir = repo_root / "output" / episode_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    transcript_cache = artifacts_dir / "transcript.json"
    transcript = _load_cached_transcript(transcript_cache, manifest.audio_path)
    if transcript is None:
        transcript = asr.transcribe(manifest)
        _save_cached_transcript(transcript_cache, manifest.audio_path, transcript)

    storybeats = hooks.build_hooks(transcript)
    scene_plan = plan_scenes(manifest, storybeats)
    render_plan = _slice_scene_plan(scene_plan, from_scene, to_scene)

    renderer.render(scene_plan=render_plan, output_dir=str(artifacts_dir), manifest=manifest)
    _write_overrides_template(scene_plan, artifacts_dir)
    _run_qc(artifacts_dir, manifest.audio_path)

    (artifacts_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "episode_id": episode_id,
                "asr_provider": settings.asr_provider,
                "hooks_provider": settings.hooks_provider,
                "render_provider": settings.render_provider,
                "scene_count": len(scene_plan.scenes),
                "render_scene_count": len(render_plan.scenes),
                "transcript_cache": str(transcript_cache),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
