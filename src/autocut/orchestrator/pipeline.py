from __future__ import annotations

import json
from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import (
    get_asr_connector,
    get_hooks_connector,
    get_render_connector,
)
from autocut.io.manifest import load_manifest
from autocut.render.scene_plan import plan_scenes


def run_pipeline(repo_root: Path, episode_id: str, settings: ProviderSettings | None = None) -> None:
    settings = settings or ProviderSettings.from_env()
    manifest = load_manifest(repo_root, episode_id)

    asr = get_asr_connector(settings)
    hooks = get_hooks_connector(settings)
    renderer = get_render_connector(settings)

    transcript = asr.transcribe(manifest)
    storybeats = hooks.build_hooks(transcript)
    scene_plan = plan_scenes(manifest, storybeats)

    artifacts_dir = repo_root / "output" / episode_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    renderer.render(scene_plan=scene_plan, output_dir=str(artifacts_dir))

    (artifacts_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "episode_id": episode_id,
                "asr_provider": settings.asr_provider,
                "hooks_provider": settings.hooks_provider,
                "render_provider": settings.render_provider,
                "scene_count": len(scene_plan.scenes),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
