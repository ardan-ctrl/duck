from autocut.config.settings import ProviderSettings
from autocut.connectors.providers import LocalOllamaHooksConnector, _rules_refine_headline


def test_rules_refine_avoids_repetition() -> None:
    h1 = _rules_refine_headline("почему ошибка")
    h2 = _rules_refine_headline("почему ошибка", previous=h1)
    assert h1 != h2


def test_ollama_parser_handles_json_payload() -> None:
    connector = LocalOllamaHooksConnector(ProviderSettings())
    parsed = connector._parse_headline('{"headline":"ПОЧЕМУ ОШИБКА"}')
    assert parsed == "ПОЧЕМУ ОШИБКА"
