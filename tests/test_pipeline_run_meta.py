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
    (episode_dir / "voice.wav").write_bytes(b"dummy")
    (episode_dir / "slide.png").write_bytes(b"dummy")

    run_pipeline(repo_root=repo_root, episode_id=episode_id, settings=ProviderSettings())

    artifacts = repo_root / "output" / episode_id / "artifacts"
    assert (artifacts / "run_meta.json").exists()
    assert (artifacts / "scene_plan_preview.txt").exists()
    assert (artifacts / "overrides_template.json").exists()
    assert (artifacts / "qc_report.json").exists()
    assert (artifacts / "transcript.json").exists()
