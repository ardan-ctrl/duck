from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.orchestrator.pipeline import run_pipeline


def test_pipeline_writes_run_meta(tmp_path: Path) -> None:
    repo_root = tmp_path
    episode_id = "ep1"

    episode_dir = repo_root / "input" / episode_id
    episode_dir.mkdir(parents=True)
    (episode_dir / "episode_manifest.json").write_text(
        '{"audio":"voice.wav","script":"script.txt","visuals":["slide.png"]}',
        encoding="utf-8",
    )
    (episode_dir / "script.txt").write_text("one. two.", encoding="utf-8")
    (episode_dir / "voice.wav").write_bytes(b"")
    (episode_dir / "slide.png").write_bytes(b"")

    run_pipeline(repo_root=repo_root, episode_id=episode_id, settings=ProviderSettings())

    meta = repo_root / "output" / episode_id / "artifacts" / "run_meta.json"
    preview = repo_root / "output" / episode_id / "artifacts" / "scene_plan_preview.txt"
    assert meta.exists()
    assert preview.exists()
