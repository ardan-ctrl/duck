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
- `--asr-provider script_stub | faster_whisper_local`
- `--hooks-provider rules_stub | ollama_local`
- `--render-provider preview_stub | remotion_local | ffmpeg_local`

### Вариант B (красивее анимация текста)

- Python = оркестратор.
- Remotion (локально) = рендер сцен.
- FFmpeg = финальный mux/concat.
- Локальная LLM через Ollama = смысловые титры.
- Локальный ASR через faster-whisper = реальные таймкоды речи.

Пример запуска:

```bash
python scripts/run_pipeline.py \
  --episode episode_demo \
  --asr-provider faster_whisper_local \
  --hooks-provider ollama_local \
  --render-provider ffmpeg_local
```

Если `npx remotion`, `ollama` или `ffmpeg` недоступны, пайплайн не падает: пишет fallback-артефакт.
При `--render-provider ffmpeg_local` коннектор пытается собрать `final.mp4` из сцен.

## Быстрый процесс для нового ролика

1. Положить файлы в `input/<episode_id>/`.
2. Заполнить `episode_manifest.json`.
3. (Опционально) добавить `overrides` внутри манифеста для ручных точечных правок.
4. Запустить `scripts/run_pipeline.py` с нужными провайдерами.
5. Проверить артефакты в `output/<episode_id>/artifacts`.

Пример `overrides` в `episode_manifest.json`:

```json
{
  "overrides": [
    {"scene_index": 0, "headline": "ПЕРЕПИСАННЫЙ ХУК"},
    {"scene_index": 2, "visual_ref": "my_custom_slide.png"}
  ]
}
```

## Статусы этапов (MVP)

- [x] Скелет проекта и контракты данных.
- [x] Плагинная схема провайдеров.
- [x] Локальный LLM-хук через Ollama (с fallback).
- [x] Локальный Remotion/FFmpeg коннектор (с fallback).
- [x] Scene overrides для ручной точечной правки.
- [ ] Финальный стиль маскотов и motion-шаблонов под production.
