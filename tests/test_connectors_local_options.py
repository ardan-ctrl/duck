from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import get_asr_connector, get_hooks_connector, get_render_connector
from autocut.models import ScenePlan


def test_ollama_hooks_connector_fallback_without_service() -> None:
    settings = ProviderSettings(hooks_provider="ollama_local", ollama_url="http://127.0.0.1:9")
    connector = get_hooks_connector(settings)
    beats = connector.build_hooks([])
    assert beats == []


def test_remotion_connector_fallback_creates_preview(tmp_path: Path) -> None:
    settings = ProviderSettings(render_provider="remotion_local")
    connector = get_render_connector(settings)
    scene_plan = ScenePlan(episode_id="e1", scenes=[])
    output_path = connector.render(scene_plan, str(tmp_path))
    assert Path(output_path).exists()
    assert (tmp_path / "render_outputs.json").exists()


def test_ffmpeg_connector_returns_artifact(tmp_path: Path) -> None:
    settings = ProviderSettings(render_provider="ffmpeg_local")
    connector = get_render_connector(settings)
    scene_plan = ScenePlan(episode_id="e1", scenes=[])
    output_path = connector.render(scene_plan, str(tmp_path))
    assert Path(output_path).exists()
    assert (tmp_path / "render_outputs.json").exists()


def test_faster_whisper_connector_falls_back_to_stub(tmp_path: Path) -> None:
    from autocut.models import EpisodeManifest

    ep_dir = tmp_path / "ep"
    ep_dir.mkdir()
    script = ep_dir / "script.txt"
    script.write_text("hello. world.", encoding="utf-8")
    audio = ep_dir / "voice.wav"
    audio.write_bytes(b"")

    settings = ProviderSettings(asr_provider="faster_whisper_local")
    connector = get_asr_connector(settings)
    manifest = EpisodeManifest(episode_id="e", audio_path=audio, script_path=script)
    segments = connector.transcribe(manifest)
    assert len(segments) >= 1
