from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SceneOverride:
    scene_index: int
    headline: str | None = None
    visual_ref: str | None = None
    start_s: float | None = None
    end_s: float | None = None
    mascot_action: str | None = None


@dataclass
class EpisodeManifest:
    episode_id: str
    audio_path: Path
    script_path: Path
    visuals: list[Path] = field(default_factory=list)
    style_id: str = "default_style"
    music_path: Path | None = None
    overrides: list[SceneOverride] = field(default_factory=list)


@dataclass
class TranscriptSegment:
    start_s: float
    end_s: float
    text: str


@dataclass
class StoryBeat:
    start_s: float
    end_s: float
    headline: str
    annotation: str | None = None


@dataclass
class Scene:
    start_s: float
    end_s: float
    visual_ref: str
    headline: str
    mascot_action: str | None = None


@dataclass
class ScenePlan:
    episode_id: str
    scenes: list[Scene] = field(default_factory=list)
