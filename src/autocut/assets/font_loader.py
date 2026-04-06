from __future__ import annotations

import re
from pathlib import Path
from urllib import request

FONT_CACHE = Path("~/.cache/autocut/fonts").expanduser()


def _extract_font_asset_url(css_text: str) -> str | None:
    for match in re.finditer(r"url\(([^)]+)\)", css_text):
        raw = match.group(1).strip().strip("\"'")
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
    return None


def _download_to_path(url: str, out_path: Path) -> None:
    with request.urlopen(url, timeout=30) as resp:  # nosec B310
        data = resp.read()
    out_path.write_bytes(data)


def download_font(google_fonts_url: str, out_path: Path) -> Path:
    req = request.Request(
        google_fonts_url,
        headers={"User-Agent": "Mozilla/5.0 (AutoCut Font Loader)"},
    )
    with request.urlopen(req, timeout=30) as resp:  # nosec B310
        css = resp.read().decode("utf-8", errors="ignore")

    asset_url = _extract_font_asset_url(css)
    if not asset_url:
        raise ValueError("Unable to find font asset URL in Google Fonts CSS response")

    _download_to_path(asset_url, out_path)
    return out_path


def resolve_font(font_config: dict) -> Path | None:
    family = str(font_config.get("family", "")).strip()
    direct_url = str(font_config.get("google_fonts_url", "")).strip()
    if not family or not direct_url:
        return None

    suffix = ".ttf"
    if ".otf" in direct_url:
        suffix = ".otf"
    elif ".woff2" in direct_url:
        suffix = ".woff2"

    safe_family = re.sub(r"[^A-Za-z0-9._-]+", "_", family)
    cached = FONT_CACHE / f"{safe_family}{suffix}"
    if cached.exists():
        return cached

    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        return download_font(direct_url, cached)
    except Exception:
        return None
