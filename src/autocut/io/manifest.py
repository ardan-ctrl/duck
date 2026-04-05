from __future__ import annotations

import json
from pathlib import Path

from autocut.models import EpisodeManifest, SceneOverride


def load_manifest(repo_root: Path, episode_id: str) -> EpisodeManifest:
    episode_dir = repo_root / "input" / episode_id
    manifest_path = episode_dir / "episode_manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    overrides: list[SceneOverride] = []
    for item in raw.get("overrides", []):
        overrides.append(
            SceneOverride(
                scene_index=int(item["scene_index"]),
                headline=item.get("headline"),
                visual_ref=item.get("visual_ref"),
                start_s=item.get("start_s"),
                end_s=item.get("end_s"),
                mascot_action=item.get("mascot_action"),
            )
        )

    return EpisodeManifest(
        episode_id=episode_id,
        audio_path=episode_dir / raw["audio"],
        script_path=episode_dir / raw["script"],
        visuals=[episode_dir / p for p in raw.get("visuals", [])],
        style_id=raw.get("style_id", "default_style"),
        overrides=overrides,
    )
