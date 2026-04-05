from __future__ import annotations

import json
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
    def render(self, scene_plan: ScenePlan, output_dir: str) -> str:
        output_path = Path(output_dir) / "scene_plan_preview.txt"
        output_path.write_text(
            "\n".join(
                f"[{s.start_s:.2f}-{s.end_s:.2f}] {s.headline} -> {s.visual_ref}"
                for s in scene_plan.scenes
            ),
            encoding="utf-8",
        )
        return str(output_path)


class LocalRemotionRenderConnector(RenderConnector):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def render(self, scene_plan: ScenePlan, output_dir: str) -> str:
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
    def render(self, scene_plan: ScenePlan, output_dir: str) -> str:
        out_dir = Path(output_dir)
        placeholder = out_dir / "ffmpeg_mux_preview.txt"
        cmd = ["ffmpeg", "-version"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            placeholder.write_text(
                "FFmpeg detected. Implement final concat/mix graph next.", encoding="utf-8"
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            placeholder.write_text("FFmpeg not found. Install ffmpeg to enable mux stage.", encoding="utf-8")
        return str(placeholder)


def get_asr_connector(settings: ProviderSettings) -> ASRConnector:
    if settings.asr_provider == "script_stub":
        return ScriptASRConnector()
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
