from __future__ import annotations

from pathlib import Path

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


def get_asr_connector(settings: ProviderSettings) -> ASRConnector:
    if settings.asr_provider == "script_stub":
        return ScriptASRConnector()
    raise ValueError(f"Unsupported ASR provider: {settings.asr_provider}")


def get_hooks_connector(settings: ProviderSettings) -> HooksConnector:
    if settings.hooks_provider == "rules_stub":
        return RulesHooksConnector()
    raise ValueError(f"Unsupported hooks provider: {settings.hooks_provider}")


def get_render_connector(settings: ProviderSettings) -> RenderConnector:
    if settings.render_provider == "preview_stub":
        return PreviewRenderConnector()
    raise ValueError(f"Unsupported render provider: {settings.render_provider}")
