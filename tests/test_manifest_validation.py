from pathlib import Path

import pytest

from autocut.io.manifest import load_manifest
from autocut.io.validation import ManifestValidationError, ensure_valid_manifest
from autocut.models import EpisodeManifest


def test_manifest_validation_raises_for_missing_files(tmp_path: Path) -> None:
    manifest = EpisodeManifest(
        episode_id="ep",
        audio_path=tmp_path / "missing.wav",
        script_path=tmp_path / "missing.txt",
        visuals=[tmp_path / "missing.png"],
    )

    with pytest.raises(ManifestValidationError):
        ensure_valid_manifest(manifest)


def test_manifest_schema_validation_for_visuals_type(tmp_path: Path) -> None:
    ep = tmp_path / "input" / "e"
    ep.mkdir(parents=True)
    (ep / "episode_manifest.json").write_text(
        '{"audio":"a.wav","script":"s.txt","visuals":"wrong-type"}',
        encoding="utf-8",
    )
    with pytest.raises(ManifestValidationError):
        load_manifest(tmp_path, "e")


def test_manifest_schema_validation_for_extra_media_type(tmp_path: Path) -> None:
    ep = tmp_path / "input" / "e2"
    ep.mkdir(parents=True)
    (ep / "episode_manifest.json").write_text(
        '{"audio":"a.wav","script":"s.txt","visuals":[],"extra_media":"wrong-type"}',
        encoding="utf-8",
    )
    with pytest.raises(ManifestValidationError):
        load_manifest(tmp_path, "e2")
