from __future__ import annotations

import re

from autocut.models import StoryBeat, TranscriptSegment

TRIGGERS = {"почему", "ошибка", "секрет", "важно", "быстро", "нельзя", "никогда"}
STOP = {"это", "как", "что", "когда", "тогда", "очень", "просто", "будет", "который"}


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[\w-]+", text.lower(), flags=re.UNICODE) if w]


def _score_word(word: str) -> int:
    if word in TRIGGERS:
        return 100
    if len(word) >= 7:
        return 15
    if len(word) >= 5:
        return 8
    return 2


def _make_headline(text: str) -> str:
    tokens = [t for t in _tokenize(text) if t not in STOP]
    if not tokens:
        tokens = _tokenize(text)
    if not tokens:
        return "КЛЮЧЕВАЯ МЫСЛЬ"

    ranked = sorted(tokens, key=_score_word, reverse=True)
    # keep ordering from original phrase for readability
    top = set(ranked[:6])
    ordered = [t for t in tokens if t in top]

    words = ordered[:6] if ordered else ranked[:6]
    if len(words) < 2:
        words.append("факт")
    return " ".join(words).upper()


def build_storybeats(transcript: list[TranscriptSegment]) -> list[StoryBeat]:
    beats: list[StoryBeat] = []
    prev: str | None = None
    for seg in transcript:
        head = _make_headline(seg.text)
        if prev == head:
            head = f"{head} СЕЙЧАС"
        prev = head

        beats.append(
            StoryBeat(
                start_s=seg.start_s,
                end_s=seg.end_s,
                headline=head,
                annotation=None,
            )
        )
    return beats
