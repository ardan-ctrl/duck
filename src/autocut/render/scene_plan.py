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
    return ScenePlan(episode_id=manifest.episode_id, scenes=scenes)
