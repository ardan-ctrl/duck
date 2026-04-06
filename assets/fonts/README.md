# Fonts (local only)

This repo keeps font binaries out of git to avoid PR merge issues with binary files.

Expected files for `serial_reference_style`:
- `Headline-Bold.ttf`
- `Scribble-MonoItalic.ttf`

Run:

```bash
bash scripts/setup_local_assets.sh
```

It will copy fallback fonts from system locations if available.
