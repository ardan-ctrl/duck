from __future__ import annotations

from pathlib import Path

from autocut.models import EpisodeManifest


class ManifestValidationError(ValueError):
    pass


def validate_manifest_raw(raw: dict) -> list[str]:
    errors: list[str] = []

    required = ["audio", "script", "visuals"]
    for key in required:
        if key not in raw:
            errors.append(f"missing required field: {key}")

    if "visuals" in raw and not isinstance(raw["visuals"], list):
        errors.append("visuals must be a list")
    if "extra_media" in raw and not isinstance(raw["extra_media"], list):
        errors.append("extra_media must be a list")

    if "overrides" in raw and not isinstance(raw["overrides"], list):
        errors.append("overrides must be a list")

    if "style_id" in raw and not isinstance(raw["style_id"], str):
        errors.append("style_id must be a string")

    return errors


def validate_manifest(manifest: EpisodeManifest) -> list[str]:
    errors: list[str] = []

    if not manifest.script_path.exists():
        errors.append(f"script file not found: {manifest.script_path}")
    if not manifest.audio_path.exists():
        errors.append(f"audio file not found: {manifest.audio_path}")
    if not manifest.visuals:
        errors.append("no visuals configured")

    for i, visual in enumerate([*manifest.visuals, *manifest.extra_media]):
        if not Path(visual).exists():
            errors.append(f"media[{i}] not found: {visual}")

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
