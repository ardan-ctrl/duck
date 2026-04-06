from pathlib import Path

from autocut.analysis.transcribe import transcribe_audio
from autocut.connectors.providers import RulesHooksConnector
from autocut.models import EpisodeManifest, TranscriptSegment


def test_transcribe_fallback_adaptive_chunks(tmp_path: Path) -> None:
    script = tmp_path / "script.txt"
    script.write_text(
        "Это очень длинное предложение без нормальной паузы которое должно разбиться на несколько кусков для тайминга.",
        encoding="utf-8",
    )
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"")

    manifest = EpisodeManifest(episode_id="e", audio_path=audio, script_path=script)
    segments = transcribe_audio(manifest)

    assert len(segments) >= 2
    assert all(s.end_s > s.start_s for s in segments)


def test_rules_hooks_remove_repeats_and_prioritize_triggers() -> None:
    connector = RulesHooksConnector()
    transcript = [
        TranscriptSegment(0, 1, "почему ошибка"),
        TranscriptSegment(1, 2, "почему ошибка"),
    ]
    beats = connector.build_hooks(transcript)
    assert beats[0].headline.startswith("ПОЧЕМУ")
    assert beats[0].headline != beats[1].headline
