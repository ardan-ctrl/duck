from __future__ import annotations

import json
from pathlib import Path

from autocut.models import EpisodeManifest


def load_manifest(repo_root: Path, episode_id: str) -> EpisodeManifest:
    episode_dir = repo_root / "input" / episode_id
    manifest_path = episode_dir / "episode_manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    return EpisodeManifest(
        episode_id=episode_id,
        audio_path=episode_dir / raw["audio"],
        script_path=episode_dir / raw["script"],
        visuals=[episode_dir / p for p in raw.get("visuals", [])],
        style_id=raw.get("style_id", "default_style"),
    )
