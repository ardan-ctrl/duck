from __future__ import annotations

from autocut.models import EpisodeManifest, TranscriptSegment


def transcribe_audio(manifest: EpisodeManifest) -> list[TranscriptSegment]:
    """Stub: replace with Whisper/other ASR integration."""
    script = manifest.script_path.read_text(encoding="utf-8").strip()
    if not script:
        return []

    chunks = [c.strip() for c in script.split(".") if c.strip()]
    dur = 3.0
    result: list[TranscriptSegment] = []
    t = 0.0
    for chunk in chunks:
        result.append(TranscriptSegment(start_s=t, end_s=t + dur, text=chunk))
        t += dur
    return result
