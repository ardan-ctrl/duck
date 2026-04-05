# AutoCut Serial Reels

Проект для автоматической сборки коротких вертикальных видео (Reels/TikTok/Shorts) из:
- озвучки,
- сценария,
- набора слайдов/клипов,
- бренд-ассетов (маскоты, графические элементы, шрифты, шаблоны).

## Цели

1. Один раз собрать "библиотеку стиля".
2. На каждый новый ролик подавать только контент и сценарий.
3. Получать готовый рендер в фирменной стилистике.

## Структура

```text
assets/              # Статические бренд-ассеты
input/               # Входные данные для конкретных выпусков
output/              # Срендеренные ролики и промежуточные файлы
src/autocut/         # Код пайплайна
templates/           # Шаблоны сцен, анимаций, стилей
docs/                # Описание архитектуры и правил
scripts/             # CLI-скрипты для запуска стадий
tests/               # Тесты
```

## Локальные провайдеры/коннекторы (без подписок)

Поддерживаемые значения:
- `--asr-provider script_stub`
- `--hooks-provider rules_stub | ollama_local`
- `--render-provider preview_stub | remotion_local | ffmpeg_local`

### Вариант B (красивее анимация текста)

- Python = оркестратор.
- Remotion (локально) = рендер сцен.
- FFmpeg = финальный mux/concat.
- Локальная LLM через Ollama = смысловые титры.

Пример запуска:

```bash
python scripts/run_pipeline.py \
  --episode episode_demo \
  --asr-provider script_stub \
  --hooks-provider ollama_local \
  --render-provider remotion_local
```

Если `npx remotion`, `ollama` или `ffmpeg` недоступны, пайплайн не падает: пишет fallback-артефакт.
При `--render-provider ffmpeg_local` коннектор пытается собрать `final.mp4` из сцен.

## Быстрый процесс для нового ролика

1. Положить файлы в `input/<episode_id>/`.
2. Заполнить `episode_manifest.json`.
3. Запустить `scripts/run_pipeline.py` с нужными провайдерами.
4. Проверить артефакты в `output/<episode_id>/artifacts`.

## Статусы этапов (MVP)

- [x] Скелет проекта и контракты данных.
- [x] Плагинная схема провайдеров.
- [x] Локальный LLM-хук через Ollama (с fallback).
- [x] Локальный Remotion/FFmpeg коннектор (с fallback).
- [ ] Реальный ASR + таймкоды.
- [ ] Компоновка сцен и маскотов.
- [ ] Финальный MP4 mux/render.
