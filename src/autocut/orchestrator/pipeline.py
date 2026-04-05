from __future__ import annotations

from pathlib import Path

from autocut.analysis.storybeat import build_storybeats
from autocut.analysis.transcribe import transcribe_audio
from autocut.io.manifest import load_manifest
from autocut.render.scene_plan import plan_scenes


def run_pipeline(repo_root: Path, episode_id: str) -> None:
    manifest = load_manifest(repo_root, episode_id)

    transcript = transcribe_audio(manifest)
    storybeats = build_storybeats(transcript)
    scene_plan = plan_scenes(manifest, storybeats)

    artifacts_dir = repo_root / "output" / episode_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "scene_plan_preview.txt").write_text(
        "\n".join(
            f"[{s.start_s:.2f}-{s.end_s:.2f}] {s.headline} -> {s.visual_ref}"
            for s in scene_plan.scenes
        ),
        encoding="utf-8",
    )
