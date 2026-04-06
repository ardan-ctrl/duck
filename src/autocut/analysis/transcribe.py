from __future__ import annotations

import re

from autocut.models import EpisodeManifest, TranscriptSegment


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _normalize_chunks(sentences: list[str], max_words: int = 12) -> list[str]:
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            chunks.append(sentence)
            continue

        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i : i + max_words]))
    return chunks


def transcribe_audio(manifest: EpisodeManifest) -> list[TranscriptSegment]:
    """Fallback transcription from script text with adaptive chunk timing."""
    script = manifest.script_path.read_text(encoding="utf-8").strip()
    if not script:
        return []

    sentences = _split_sentences(script)
    chunks = _normalize_chunks(sentences)
    total_words = sum(max(1, len(c.split())) for c in chunks)

    # Aim for ~2.4 words/sec, with per-chunk limits.
    wps = 2.4
    result: list[TranscriptSegment] = []
    t = 0.0
    for chunk in chunks:
        words = max(1, len(chunk.split()))
        dur = max(1.1, min(6.0, words / wps))
        result.append(TranscriptSegment(start_s=t, end_s=t + dur, text=chunk))
        t += dur

    if not result and total_words > 0:
        result.append(TranscriptSegment(start_s=0.0, end_s=max(1.2, total_words / wps), text=script))
    return result
