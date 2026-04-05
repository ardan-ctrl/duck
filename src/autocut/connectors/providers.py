from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from urllib import request

from autocut.analysis.storybeat import build_storybeats
from autocut.analysis.transcribe import transcribe_audio
from autocut.config.settings import ProviderSettings
from autocut.connectors.base import ASRConnector, HooksConnector, RenderConnector
from autocut.models import EpisodeManifest, ScenePlan, StoryBeat, TranscriptSegment


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
                txt = (seg.text or '').strip()
                if not txt:
                    continue
                result.append(TranscriptSegment(start_s=float(seg.start), end_s=float(seg.end), text=txt))
            return result or transcribe_audio(manifest)
        except Exception:
            return transcribe_audio(manifest)


class RulesHooksConnector(HooksConnector):
    def build_hooks(self, transcript: list[TranscriptSegment]) -> list[StoryBeat]:
        return build_storybeats(transcript)


class LocalOllamaHooksConnector(HooksConnector):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def _headline_from_llm(self, text: str) -> str:
        prompt = (
            "Сделай короткий заголовок (2-6 слов, CAPS) для видео-титра. "
            "Верни только одну строку без пояснений. Текст: " + text
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
        with request.urlopen(req, timeout=20) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
        return (data.get("response") or "").strip().upper()[:80]

    def build_hooks(self, transcript: list[TranscriptSegment]) -> list[StoryBeat]:
        beats: list[StoryBeat] = []
        for seg in transcript:
            try:
                headline = self._headline_from_llm(seg.text)
                if not headline:
                    headline = " ".join(seg.text.split()[:4]).upper()
            except Exception:
                headline = " ".join(seg.text.split()[:4]).upper()

            beats.append(StoryBeat(start_s=seg.start_s, end_s=seg.end_s, headline=headline))
        return beats


class PreviewRenderConnector(RenderConnector):
    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        output_path = Path(output_dir) / "scene_plan_preview.txt"
        output_path.write_text(
            "\n".join(
                f"[{s.start_s:.2f}-{s.end_s:.2f}] {s.headline} -> {Path(s.visual_ref).name}"
                for s in scene_plan.scenes
            ),
            encoding="utf-8",
        )
        return str(output_path)


class LocalRemotionRenderConnector(RenderConnector):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        out_dir = Path(output_dir)
        props_path = out_dir / "remotion_props.json"
        out_video = out_dir / "remotion_render.mp4"

        props_path.write_text(
            json.dumps(
                {
                    "episode_id": scene_plan.episode_id,
                    "fps": self.settings.remotion_fps,
                    "width": self.settings.remotion_width,
                    "height": self.settings.remotion_height,
                    "scenes": [s.__dict__ for s in scene_plan.scenes],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        cmd = [
            "npx",
            "remotion",
            "render",
            self.settings.remotion_entry,
            self.settings.remotion_composition,
            str(out_video),
            "--props",
            str(props_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return str(out_video)
        except (FileNotFoundError, subprocess.CalledProcessError):
            fallback = out_dir / "scene_plan_preview.txt"
            fallback.write_text("Remotion unavailable, fallback preview generated.", encoding="utf-8")
            return str(fallback)


class LocalFfmpegMuxConnector(RenderConnector):
    def _scene_duration(self, start_s: float, end_s: float) -> float:
        return max(0.8, end_s - start_s)

    def _run(self, cmd: list[str]) -> None:
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    def _create_scene_clip(self, scene, clip_path: Path, width: int = 1080, height: int = 1920) -> None:
        duration = self._scene_duration(scene.start_s, scene.end_s)
        visual = Path(scene.visual_ref)
        safe_headline = scene.headline.replace("'", "")[:50]

        if visual.exists() and visual.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-t",
                f"{duration:.2f}",
                "-i",
                str(visual),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=cover,crop={width}:{height},drawtext=text='{safe_headline}':x=(w-text_w)/2:y=120:fontsize=78:fontcolor=white:box=1:boxcolor=black@0.35:boxborderw=20",
                "-r",
                "30",
                str(clip_path),
            ]
        elif visual.exists() and visual.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
            cmd = [
                "ffmpeg",
                "-y",
                "-stream_loop",
                "-1",
                "-t",
                f"{duration:.2f}",
                "-i",
                str(visual),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=cover,crop={width}:{height},drawtext=text='{safe_headline}':x=(w-text_w)/2:y=120:fontsize=78:fontcolor=white:box=1:boxcolor=black@0.35:boxborderw=20",
                "-r",
                "30",
                str(clip_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-t",
                f"{duration:.2f}",
                "-i",
                f"color=c=black:s={width}x{height}:r=30",
                "-vf",
                f"drawtext=text='{safe_headline}':x=(w-text_w)/2:y=120:fontsize=78:fontcolor=white:box=1:boxcolor=black@0.35:boxborderw=20",
                str(clip_path),
            ]
        self._run(cmd)

    def render(self, scene_plan: ScenePlan, output_dir: str, manifest: EpisodeManifest | None = None) -> str:
        out_dir = Path(output_dir)
        temp_dir = out_dir / "tmp_clips"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._run(["ffmpeg", "-version"])
        except (FileNotFoundError, subprocess.CalledProcessError):
            placeholder = out_dir / "ffmpeg_mux_preview.txt"
            placeholder.write_text("FFmpeg not found. Install ffmpeg to enable mux stage.", encoding="utf-8")
            return str(placeholder)

        concat_list = out_dir / "concat_list.txt"
        entries: list[str] = []

        for idx, scene in enumerate(scene_plan.scenes):
            clip_path = temp_dir / f"scene_{idx:03d}.mp4"
            self._create_scene_clip(scene, clip_path)
            entries.append(f"file {shlex.quote(str(clip_path.resolve()))}")

        concat_list.write_text("\n".join(entries), encoding="utf-8")

        stitched = out_dir / "stitched.mp4"
        self._run([
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(stitched),
        ])

        final_path = out_dir / "final.mp4"
        if manifest and manifest.audio_path.exists() and manifest.audio_path.stat().st_size > 0:
            self._run([
                "ffmpeg",
                "-y",
                "-i",
                str(stitched),
                "-i",
                str(manifest.audio_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                str(final_path),
            ])
        else:
            stitched.replace(final_path)
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
