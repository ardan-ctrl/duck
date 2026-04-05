from pathlib import Path

from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import get_hooks_connector, get_render_connector
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
