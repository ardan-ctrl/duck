from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from urllib import request

from autocut.analysis.storybeat import build_storybeats
from autocut.analysis.transcribe import transcribe_audio
from autocut.config.settings import ProviderSettings
from autocut.connectors.base import ASRConnector, HooksConnector, RenderConnector
from autocut.models import EpisodeManifest, ScenePlan, StoryBeat, TranscriptSegment


def quality_gate_headline(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]+", " ", text, flags=re.UNICODE)
    words = [w for w in cleaned.split() if w]
    if not words:
        return "КЛЮЧЕВАЯ МЫСЛЬ"
    words = words[:6]
    if len(words) < 2:
        words.append("ФАКТ")
    return " ".join(words).upper()[:80]


BLACKLIST_WORDS = {"НУ", "КАК БЫ", "ВООБЩЕ", "В ЦЕЛОМ"}
TRIGGER_WORDS = {"ПОЧЕМУ", "ОШИБКА", "СЕКРЕТ", "НИКОГДА", "СРАЗУ", "ВАЖНО"}
BANNED_HOOKS = {"КЛЮЧЕВАЯ МЫСЛЬ ФАКТ", "ФАКТ ФАКТ"}


def _rules_refine_headline(base: str, previous: str | None = None) -> str:
    head = quality_gate_headline(base)
    words = [w for w in head.split() if w and w not in BLACKLIST_WORDS]
    if not words:
        words = ["КЛЮЧЕВАЯ", "МЫСЛЬ"]

    trigger_first = [w for w in words if w in TRIGGER_WORDS]
    rest = [w for w in words if w not in TRIGGER_WORDS]
    ordered = (trigger_first + rest)[:6]
    candidate = " ".join(ordered)

    if previous and candidate == previous:
        candidate = (candidate + " СЕЙЧАС").strip()

    candidate = quality_gate_headline(candidate)
    if candidate in BANNED_HOOKS:
        candidate = "ВАЖНЫЙ ФАКТ"
    return candidate


class ScriptASRConnector(ASRConnector):
    def transcribe(self, manifest: EpisodeManifest) -> list[TranscriptSegment]:
        return transcribe_audio(manifest)


class FasterWhisperASRConnector(ASRConnector):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def transcribe(self, manifest: EpisodeManifest) -> list[TranscriptSegment]:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception:
            return transcribe_audio(manifest)

        if not manifest.audio_path.exists() or manifest.audio_path.stat().st_size == 0:
            return transcribe_audio(manifest)

        try:
            model = WhisperModel(self.settings.faster_whisper_model, device=self.settings.faster_whisper_device)
            segments, _info = model.transcribe(str(manifest.audio_path), vad_filter=True)
            result: list[TranscriptSegment] = []
            for seg in segments:
                txt = (seg.text or "").strip()
                if not txt:
                    continue
                result.append(TranscriptSegment(start_s=float(seg.start), end_s=float(seg.end), text=txt))
            return result or transcribe_audio(manifest)
        except Exception:
            return transcribe_audio(manifest)


class RulesHooksConnector(HooksConnector):
    def build_hooks(self, transcript: list[TranscriptSegment]) -> list[StoryBeat]:
        beats = build_storybeats(transcript)
        previous: str | None = None
        for beat in beats:
            beat.headline = _rules_refine_headline(beat.headline, previous=previous)
            previous = beat.headline
        return beats


class LocalOllamaHooksConnector(HooksConnector):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def _query_ollama(self, text: str) -> str:
        prompt = (
            "Верни JSON {\"headline\":\"...\"}. "
            "headline: 2-6 слов, CAPS, без пунктуации и без пояснений. "
            f"Текст: {text}"
        )
        payload = json.dumps(
            {
                "model": self.settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")

        req = request.Request(
            url=f"{self.settings.ollama_url}/api/generate",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        with request.urlopen(req, timeout=25) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("response") or ""

    def _parse_headline(self, raw: str) -> str:
        raw = raw.strip()
        # Try JSON first
        try:
            maybe = json.loads(raw)
            if isinstance(maybe, dict) and "headline" in maybe:
                return str(maybe["headline"])
        except Exception:
            pass

        # Extract JSON object from noisy text
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                maybe = json.loads(m.group(0))
                if isinstance(maybe, dict) and "headline" in maybe:
                    return str(maybe["headline"])
            except Exception:
                pass

        # Fallback to raw text line
        first_line = raw.splitlines()[0] if raw else ""
        return first_line

    def build_hooks(self, transcript: list[TranscriptSegment]) -> list[StoryBeat]:
        beats: list[StoryBeat] = []
        previous: str | None = None

        for seg in transcript:
            headline = ""
            for _ in range(2):
                try:
                    response = self._query_ollama(seg.text)
                    parsed = self._parse_headline(response)
                    headline = _rules_refine_headline(parsed, previous=previous)
                    break
                except Exception:
                    time.sleep(0.2)

            if not headline:
                headline = _rules_refine_headline(seg.text, previous=previous)

            previous = headline
            beats.append(StoryBeat(start_s=seg.start_s, end_s=seg.end_s, headline=headline))
        return beats


class PreviewRenderConnector(RenderConnector):
    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        output_path = Path(output_dir) / "scene_plan_preview.txt"
        output_path.write_text(
            "\n".join(
                f"[{scene.start_s:.2f}-{scene.end_s:.2f}] {scene.headline} -> {Path(scene.visual_ref).name}"
                for scene in scene_plan.scenes
            ),
            encoding="utf-8",
        )
        return str(output_path)


class LocalRemotionRenderConnector(RenderConnector):
    """Production-oriented remotion path with resilient fallback to ffmpeg renderer."""

    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def _render_variant(self, props_path: Path, out_video: Path, variant: str) -> None:
        cmd = [
            "npx",
            "remotion",
            "render",
            self.settings.remotion_entry,
            self.settings.remotion_composition,
            str(out_video),
            "--props",
            str(props_path),
            "--codec",
            "h264",
        ]
        env = {**os.environ, **{"AUTOCUT_VARIANT": variant}}
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800, env=env)

    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        out_dir = Path(output_dir)
        props_path = out_dir / "remotion_props.json"
        final_video = out_dir / "final.mp4"
        alt_video = out_dir / "alt.mp4"

        props_path.write_text(
            json.dumps(
                {
                    "episode_id": scene_plan.episode_id,
                    "fps": self.settings.remotion_fps,
                    "width": self.settings.remotion_width,
                    "height": self.settings.remotion_height,
                    "variant": "final",
                    "scenes": [s.__dict__ for s in scene_plan.scenes],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # Validate prerequisites
        if not Path(self.settings.remotion_entry).exists():
            return LocalFfmpegMuxConnector().render(scene_plan, output_dir, manifest)

        try:
            self._render_variant(props_path, final_video, "final")
            self._render_variant(props_path, alt_video, "alt")
            (out_dir / "render_outputs.json").write_text(
                json.dumps({"final": str(final_video), "alt": str(alt_video), "ducking": False}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return str(final_video)
        except Exception:
            # Production fallback to ffmpeg, not preview-only
            return LocalFfmpegMuxConnector().render(scene_plan, output_dir, manifest)


class LocalFfmpegMuxConnector(RenderConnector):
    def _scene_duration(self, start_s: float, end_s: float) -> float:
        return max(0.8, end_s - start_s)

    def _run(self, cmd: list[str]) -> None:
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    def _style_profile(self, manifest: EpisodeManifest | None) -> tuple[int, int, int, int, str | None]:
        left, right, top, bottom = 60, 60, 180, 280
        fontfile: str | None = None
        if manifest is None:
            return left, right, top, bottom, fontfile

        repo_root = manifest.script_path.parents[2]
        style_file = repo_root / "templates" / "styles" / f"{manifest.style_id}.json"
        if not style_file.exists():
            style_file = repo_root / "templates" / "styles" / "default_style.json"

        try:
            raw = json.loads(style_file.read_text(encoding="utf-8"))
            safe = raw.get("safe_zone", {})
            left = int(safe.get("left", left))
            right = int(safe.get("right", right))
            top = int(safe.get("top", top))
            bottom = int(safe.get("bottom", bottom))

            font_name = raw.get("typography", {}).get("headline_font")
            if font_name:
                candidate = repo_root / "assets" / "fonts" / font_name
                if candidate.exists():
                    fontfile = str(candidate)
        except Exception:
            pass

        return left, right, top, bottom, fontfile

    def _drawtext_filter(self, headline: str, manifest: EpisodeManifest | None, role: str) -> str:
        safe_headline = quality_gate_headline(headline).replace("'", "")[:50]
        left, _right, top, bottom, fontfile = self._style_profile(manifest)

        size = 78
        y = top
        boxcolor = "black@0.35"
        if role == "hook":
            size = 92
            y = top
            boxcolor = "black@0.45"
        elif role == "fact":
            size = 72
            y = top + 40
        elif role == "cta":
            size = 84
            y = max(top, 1920 - bottom - 200)
            boxcolor = "#d61020@0.55"

        draw = (
            f"drawtext=text='{safe_headline}':x={left}:y={y}:fontsize={size}:fontcolor=white:"
            f"box=1:boxcolor={boxcolor}:boxborderw=20"
        )
        if fontfile:
            draw += f":fontfile={fontfile}"
        return draw

    def _create_scene_clip(
        self,
        scene,
        clip_path: Path,
        width: int = 1080,
        height: int = 1920,
        manifest: EpisodeManifest | None = None,
        role: str = "fact",
    ) -> None:
        duration = self._scene_duration(scene.start_s, scene.end_s)
        visual = Path(scene.visual_ref)
        draw = self._drawtext_filter(scene.headline, manifest, role)

        if visual.exists() and visual.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(visual),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=cover,crop={width}:{height},{draw}",
                "-r", "30", str(clip_path),
            ]
        elif visual.exists() and visual.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
            cmd = [
                "ffmpeg", "-y", "-stream_loop", "-1", "-t", f"{duration:.2f}", "-i", str(visual),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=cover,crop={width}:{height},{draw}",
                "-r", "30", str(clip_path),
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-t", f"{duration:.2f}", "-i", f"color=c=black:s={width}x{height}:r=30",
                "-vf", draw, str(clip_path),
            ]
        self._run(cmd)

    def _scene_signature(self, scene) -> str:
        return f"{scene.start_s:.2f}|{scene.end_s:.2f}|{scene.visual_ref}|{scene.headline}|{scene.mascot_action or ''}"

    def _load_clip_signatures(self, out_dir: Path) -> dict[str, str]:
        sig_path = out_dir / "clip_signatures.json"
        if not sig_path.exists():
            return {}
        try:
            return json.loads(sig_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_clip_signatures(self, out_dir: Path, signatures: dict[str, str]) -> None:
        (out_dir / "clip_signatures.json").write_text(
            json.dumps(signatures, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _export_alt_version(self, final_path: Path, alt_path: Path) -> None:
        self._run([
            "ffmpeg", "-y", "-i", str(final_path),
            "-vf", "eq=contrast=1.03:saturation=1.08,drawtext=text='ALT':x=w-tw-30:y=30:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.35",
            "-c:a", "copy", str(alt_path),
        ])

    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        out_dir = Path(output_dir)
        temp_dir = out_dir / "tmp_clips"
        temp_dir.mkdir(parents=True, exist_ok=True)

        if not scene_plan.scenes:
            placeholder = out_dir / "ffmpeg_mux_preview.txt"
            placeholder.write_text(
                "Scene plan is empty. Nothing to render for ffmpeg mux stage.",
                encoding="utf-8",
            )
            (out_dir / "render_outputs.json").write_text(
                json.dumps({"final": str(placeholder), "alt": str(placeholder), "ducking": False}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return str(placeholder)

        try:
            self._run(["ffmpeg", "-version"])
        except (FileNotFoundError, subprocess.CalledProcessError):
            placeholder = out_dir / "ffmpeg_mux_preview.txt"
            placeholder.write_text("FFmpeg not found. Install ffmpeg to enable mux stage.", encoding="utf-8")
            (out_dir / "render_outputs.json").write_text(
                json.dumps({"final": str(placeholder), "alt": str(placeholder), "ducking": False}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return str(placeholder)

        concat_list = out_dir / "concat_list.txt"
        entries: list[str] = []
        previous = self._load_clip_signatures(out_dir)
        current: dict[str, str] = {}

        total = len(scene_plan.scenes)
        for idx, scene in enumerate(scene_plan.scenes):
            clip_path = temp_dir / f"scene_{idx:03d}.mp4"
            role = "hook" if idx == 0 else ("cta" if idx == total - 1 else "fact")
            sig = self._scene_signature(scene) + f"|role={role}"
            key = f"scene_{idx:03d}"
            current[key] = sig
            if previous.get(key) != sig or not clip_path.exists():
                self._create_scene_clip(scene, clip_path, manifest=manifest, role=role)
            entries.append(f"file {shlex.quote(str(clip_path.resolve()))}")

        self._save_clip_signatures(out_dir, current)
        concat_list.write_text("\n".join(entries), encoding="utf-8")

        stitched = out_dir / "stitched.mp4"
        self._run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(stitched)])

        final_path = out_dir / "final.mp4"
        has_voice = bool(manifest and manifest.audio_path.exists() and manifest.audio_path.stat().st_size > 0)
        has_music = bool(manifest and manifest.music_path and manifest.music_path.exists() and manifest.music_path.stat().st_size > 0)

        if has_voice and has_music and manifest:
            self._run([
                "ffmpeg", "-y", "-i", str(stitched), "-i", str(manifest.audio_path), "-i", str(manifest.music_path),
                "-filter_complex", "[2:a]volume=0.25[m];[m][1:a]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final_path),
            ])
        elif has_voice and manifest:
            self._run(["ffmpeg", "-y", "-i", str(stitched), "-i", str(manifest.audio_path), "-c:v", "copy", "-c:a", "aac", "-shortest", str(final_path)])
        else:
            stitched.replace(final_path)

        alt_path = out_dir / "alt.mp4"
        try:
            self._export_alt_version(final_path, alt_path)
        except Exception:
            alt_path.write_bytes(final_path.read_bytes())

        (out_dir / "render_outputs.json").write_text(
            json.dumps({"final": str(final_path), "alt": str(alt_path), "ducking": bool(has_voice and has_music)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(final_path)


def get_asr_connector(settings: ProviderSettings) -> ASRConnector:
    if settings.asr_provider == "script_stub":
        return ScriptASRConnector()
    if settings.asr_provider == "faster_whisper_local":
        return FasterWhisperASRConnector(settings)
    raise ValueError(f"Unsupported ASR provider: {settings.asr_provider}")


def get_hooks_connector(settings: ProviderSettings) -> HooksConnector:
    if settings.hooks_provider == "rules_stub":
        return RulesHooksConnector()
    if settings.hooks_provider == "ollama_local":
        return LocalOllamaHooksConnector(settings)
    raise ValueError(f"Unsupported hooks provider: {settings.hooks_provider}")


def get_render_connector(settings: ProviderSettings) -> RenderConnector:
    if settings.render_provider == "preview_stub":
        return PreviewRenderConnector()
    if settings.render_provider == "remotion_local":
        return LocalRemotionRenderConnector(settings)
    if settings.render_provider == "ffmpeg_local":
        return LocalFfmpegMuxConnector()
    raise ValueError(f"Unsupported render provider: {settings.render_provider}")
