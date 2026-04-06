from __future__ import annotations

from autocut.models import EpisodeManifest, Scene, ScenePlan, StoryBeat


def plan_scenes(manifest: EpisodeManifest, beats: list[StoryBeat]) -> ScenePlan:
    visuals = [str(p) for p in manifest.visuals] or ["fallback_background.png"]

    scenes: list[Scene] = []
    for i, beat in enumerate(beats):
        scenes.append(
            Scene(
                start_s=beat.start_s,
                end_s=beat.end_s,
                visual_ref=visuals[i % len(visuals)],
                headline=beat.headline,
                mascot_action="pop_in" if i % 3 == 0 else None,
            )
        )

    for override in manifest.overrides:
        if 0 <= override.scene_index < len(scenes):
            scene = scenes[override.scene_index]
            if override.headline is not None:
                scene.headline = override.headline
            if override.visual_ref is not None:
                scene.visual_ref = str((manifest.script_path.parent / override.visual_ref).resolve())
            if override.start_s is not None:
                scene.start_s = float(override.start_s)
            if override.end_s is not None:
                scene.end_s = float(override.end_s)
            if override.mascot_action is not None:
                scene.mascot_action = override.mascot_action

    return ScenePlan(episode_id=manifest.episode_id, scenes=scenes)
