from autocut.analysis.storybeat import build_storybeats
from autocut.models import TranscriptSegment


def test_build_storybeats_returns_one_per_segment() -> None:
    transcript = [
        TranscriptSegment(0.0, 3.0, "hello world"),
        TranscriptSegment(3.0, 6.0, "another segment"),
    ]
    beats = build_storybeats(transcript)
    assert len(beats) == 2


def test_storybeat_prioritizes_trigger_words() -> None:
    transcript = [TranscriptSegment(0.0, 3.0, "почему эта ошибка возникает снова")]
    beats = build_storybeats(transcript)
    assert "ПОЧЕМУ" in beats[0].headline or "ОШИБКА" in beats[0].headline
