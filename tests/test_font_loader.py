from pathlib import Path

from autocut.assets import font_loader


class _Resp:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_extract_font_asset_url() -> None:
    css = "@font-face{src:url(https://fonts.gstatic.com/s/font.woff2) format('woff2');}"
    assert font_loader._extract_font_asset_url(css) == "https://fonts.gstatic.com/s/font.woff2"


def test_resolve_font_uses_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(font_loader, "FONT_CACHE", tmp_path)
    cached = tmp_path / "Bebas_Neue.ttf"
    cached.write_bytes(b"font")

    cfg = {
        "family": "Bebas Neue",
        "google_fonts_url": "https://fonts.googleapis.com/css2?family=Bebas+Neue",
    }
    resolved = font_loader.resolve_font(cfg)
    assert resolved == cached


def test_resolve_font_downloads_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(font_loader, "FONT_CACHE", tmp_path)

    def fake_urlopen(req, timeout=30):  # noqa: ARG001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "fonts.googleapis.com" in url:
            return _Resp(b"@font-face{src:url(https://fonts.gstatic.com/s/font.woff2)}")
        return _Resp(b"binaryfont")

    monkeypatch.setattr(font_loader.request, "urlopen", fake_urlopen)
    cfg = {
        "family": "Lobster Two",
        "google_fonts_url": "https://fonts.googleapis.com/css2?family=Lobster+Two:wght@700",
    }
    resolved = font_loader.resolve_font(cfg)
    assert resolved is not None
    assert resolved.exists()
