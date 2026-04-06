from autocut.analysis.storybeat import build_storybeats
from autocut.models import TranscriptSegment


def test_build_storybeats_returns_one_per_segment() -> None:
    transcript = [
        TranscriptSegment(0.0, 3.0, "hello world"),
        TranscriptSegment(3.0, 6.0, "another segment"),
    ]
    beats = build_storybeats(transcript)
    assert len(beats) == 2
