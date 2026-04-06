from __future__ import annotations

from pathlib import Path

from autocut.models import EpisodeManifest


class ManifestValidationError(ValueError):
    pass


def validate_manifest(manifest: EpisodeManifest) -> list[str]:
    errors: list[str] = []

    if not manifest.script_path.exists():
        errors.append(f"script file not found: {manifest.script_path}")
    if not manifest.audio_path.exists():
        errors.append(f"audio file not found: {manifest.audio_path}")
    if not manifest.visuals:
        errors.append("no visuals configured")

    for i, visual in enumerate(manifest.visuals):
        if not Path(visual).exists():
            errors.append(f"visual[{i}] not found: {visual}")

    for ov in manifest.overrides:
        if ov.scene_index < 0:
            errors.append(f"override scene_index must be >=0, got {ov.scene_index}")
        if ov.start_s is not None and ov.end_s is not None and ov.end_s <= ov.start_s:
            errors.append(
                f"override scene_index={ov.scene_index} has invalid time range: start_s={ov.start_s}, end_s={ov.end_s}"
            )

    return errors


def ensure_valid_manifest(manifest: EpisodeManifest) -> None:
    errors = validate_manifest(manifest)
    if errors:
        joined = "\n".join(f"- {e}" for e in errors)
        raise ManifestValidationError(f"Manifest validation failed:\n{joined}")
