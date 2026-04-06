from __future__ import annotations

from autocut.models import EpisodeManifest, Scene, ScenePlan, StoryBeat


def _scene_type_for_index(idx: int, total: int) -> str:
    if idx == 0:
        return "hook"
    if idx == total - 1:
        return "cta"
    return "fact"


def plan_scenes(manifest: EpisodeManifest, beats: list[StoryBeat]) -> ScenePlan:
    visuals = [str(p) for p in [*manifest.visuals, *manifest.extra_media]] or ["fallback_background.png"]

    scenes: list[Scene] = []
    total = len(beats)
    for i, beat in enumerate(beats):
        scene_type = _scene_type_for_index(i, total)
        mascot_action = "duck_neutral" if scene_type == "hook" else None
        scenes.append(
            Scene(
                start_s=beat.start_s,
                end_s=beat.end_s,
                visual_ref=visuals[i % len(visuals)],
                headline=beat.headline,
                scene_type=scene_type,
                mascot_action=mascot_action,
                slots={
                    "headline": beat.headline,
                    "accent_top": beat.annotation or "",
                    "visual_ref": visuals[i % len(visuals)],
                    "mascot_action": mascot_action,
                },
            )
        )

    for override in manifest.overrides:
        if 0 <= override.scene_index < len(scenes):
            scene = scenes[override.scene_index]
            if override.headline is not None:
                scene.headline = override.headline
                scene.slots["headline"] = override.headline
            if override.accent_top is not None:
                scene.accent_top = override.accent_top
                scene.slots["accent_top"] = override.accent_top
            if override.visual_ref is not None:
                scene.visual_ref = str((manifest.script_path.parent / override.visual_ref).resolve())
                scene.slots["visual_ref"] = scene.visual_ref
            if override.start_s is not None:
                scene.start_s = float(override.start_s)
            if override.end_s is not None:
                scene.end_s = float(override.end_s)
            if override.mascot_action is not None:
                scene.mascot_action = override.mascot_action
                scene.slots["mascot_action"] = override.mascot_action
            if override.scene_type is not None:
                scene.scene_type = override.scene_type

    return ScenePlan(episode_id=manifest.episode_id, scenes=scenes)
