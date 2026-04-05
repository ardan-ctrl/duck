from __future__ import annotations

from autocut.models import StoryBeat, TranscriptSegment


def _make_headline(text: str) -> str:
    words = text.split()
    return " ".join(words[:4]).upper()


def build_storybeats(transcript: list[TranscriptSegment]) -> list[StoryBeat]:
    """Stub: replace with LLM extraction of semantic hooks."""
    beats: list[StoryBeat] = []
    for seg in transcript:
        beats.append(
            StoryBeat(
                start_s=seg.start_s,
                end_s=seg.end_s,
                headline=_make_headline(seg.text),
                annotation=None,
            )
        )
    return beats
