#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONT_DIR="$ROOT_DIR/assets/fonts"
mkdir -p "$FONT_DIR"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -f "$src" ]]; then
    cp "$src" "$dst"
    echo "Copied: $dst"
  else
    echo "Missing source: $src"
  fi
}

copy_if_exists "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" "$FONT_DIR/Headline-Bold.ttf"
copy_if_exists "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf" "$FONT_DIR/Scribble-MonoItalic.ttf"

echo "Done."
