from __future__ import annotations

from abc import ABC, abstractmethod

from autocut.models import EpisodeManifest, ScenePlan, StoryBeat, TranscriptSegment


class ASRConnector(ABC):
    @abstractmethod
    def transcribe(self, manifest: EpisodeManifest) -> list[TranscriptSegment]:
        raise NotImplementedError


class HooksConnector(ABC):
    @abstractmethod
    def build_hooks(self, transcript: list[TranscriptSegment]) -> list[StoryBeat]:
        raise NotImplementedError


class RenderConnector(ABC):
    @abstractmethod
    def render(self, scene_plan: ScenePlan, output_dir: str) -> str:
        raise NotImplementedError
