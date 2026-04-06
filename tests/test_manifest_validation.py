from pathlib import Path

import pytest

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
