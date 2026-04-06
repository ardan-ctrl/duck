# STYLE LIBRARY SETUP (from provided references)

Этот документ фиксирует, как собрана базовая библиотека стиля на основе референс-кадров:
- контрастные однотонные фоны (красный/синий/черный),
- крупный капс-тайп,
- рукописные overlay-акценты,
- стикеры/маскот поверх headline.

## Что уже добавлено

1. Цветовая палитра: `assets/style_pack/reference_palette.json`
2. Шрифты (локальные fallback):
   - `assets/fonts/Headline-Bold.ttf`
   - `assets/fonts/Scribble-MonoItalic.ttf`
3. Стиль-пакет: `templates/styles/serial_reference_style.json`
4. Шаблоны сцен:
   - `templates/scenes/hook_scene.json`
   - `templates/scenes/fact_scene.json`
   - `templates/scenes/cta_scene.json`
5. Motion-пресеты:
   - `templates/motions/scribble_overlay.json`
   - `templates/motions/strike_through.json`
6. Манифесты ассетов:
   - `assets/mascots/manifest.json`
   - `assets/elements/manifest.json`

## Что нужно вручную докинуть

- Реальные вырезки маскотов в `assets/mascots/`.
- Реальные декоративные PNG/WebP в `assets/elements/stickers/` и `assets/elements/overlays/`.
- При наличии брендовых шрифтов заменить fallback-файлы в `assets/fonts/`.


## Быстрая инициализация локальных шрифтов

```bash
bash scripts/setup_local_assets.sh
```
