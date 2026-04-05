from pathlib import Path

from autocut.io.manifest import load_manifest
from autocut.models import StoryBeat
from autocut.render.scene_plan import plan_scenes


def test_scene_overrides_apply(tmp_path: Path) -> None:
    repo_root = tmp_path
    episode_id = "ep_override"
    ep_dir = repo_root / "input" / episode_id
    ep_dir.mkdir(parents=True)

    (ep_dir / "script.txt").write_text("a. b.", encoding="utf-8")
    (ep_dir / "voice.wav").write_bytes(b"")
    (ep_dir / "slide.png").write_bytes(b"")
    (ep_dir / "custom.png").write_bytes(b"")
    (ep_dir / "episode_manifest.json").write_text(
        """{
        "audio": "voice.wav",
        "script": "script.txt",
        "visuals": ["slide.png"],
        "overrides": [
            {"scene_index": 0, "headline": "МОЙ ТЕКСТ", "visual_ref": "custom.png"}
        ]
    }""",
        encoding="utf-8",
    )

    manifest = load_manifest(repo_root, episode_id)
    beats = [StoryBeat(0, 2, "A"), StoryBeat(2, 4, "B")]
    plan = plan_scenes(manifest, beats)

    assert plan.scenes[0].headline == "МОЙ ТЕКСТ"
    assert plan.scenes[0].visual_ref.endswith("custom.png")
