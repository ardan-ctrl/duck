from autocut.connectors.providers import quality_gate_headline


def test_quality_gate_normalizes_and_limits_words() -> None:
    out = quality_gate_headline("  ??? один  ")
    assert out == "ОДИН ФАКТ"

    out2 = quality_gate_headline("это очень длинная фраза для теста качества заголовка")
    assert len(out2.split()) <= 6
    assert out2 == out2.upper()
