from __future__ import annotations

import json
from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import get_asr_connector, get_hooks_connector, get_render_connector
from autocut.io.manifest import load_manifest
from autocut.io.validation import ensure_valid_manifest
from autocut.render.scene_plan import plan_scenes


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


def _run_qc(artifacts_dir: Path) -> None:
    issues: list[str] = []

    final_path = artifacts_dir / "final.mp4"
    render_outputs = artifacts_dir / "render_outputs.json"

    if not final_path.exists():
        issues.append("final.mp4 is missing")
    elif final_path.stat().st_size == 0:
        issues.append("final.mp4 is empty")

    if not render_outputs.exists():
        issues.append("render_outputs.json is missing")

    status = "ok" if not issues else "warning"
    (artifacts_dir / "qc_report.json").write_text(
        json.dumps({"status": status, "issues": issues}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_pipeline(repo_root: Path, episode_id: str, settings: ProviderSettings | None = None) -> None:
    settings = settings or ProviderSettings.from_env()
    manifest = load_manifest(repo_root, episode_id)
    ensure_valid_manifest(manifest)

    asr = get_asr_connector(settings)
    hooks = get_hooks_connector(settings)
    renderer = get_render_connector(settings)

    transcript = asr.transcribe(manifest)
    storybeats = hooks.build_hooks(transcript)
    scene_plan = plan_scenes(manifest, storybeats)

    artifacts_dir = repo_root / "output" / episode_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    renderer.render(scene_plan=scene_plan, output_dir=str(artifacts_dir), manifest=manifest)
    _write_overrides_template(scene_plan, artifacts_dir)
    _run_qc(artifacts_dir)

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
