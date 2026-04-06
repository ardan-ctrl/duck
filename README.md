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

## Iteration B + C (реализовано)

- Semantic hooks quality gate.
- Музыка + ducking (voice приоритет).
- Экспорт двух версий: `final.mp4` и `alt.mp4`.
- Manifest validation с понятной ошибкой.
- Автогенерация `overrides_template.json`.
- Автоматический `qc_report.json` после рендера (включая resolution/duration checks при доступном ffprobe).
- Использование safe-zone и font профиля из `templates/styles/*.json`.
- Transcript cache: `transcript.json` (ускоряет повторные прогоны).
- Partial rerender сцен через `clip_signatures.json` (пересобираются только измененные сцены).
- 3 пресета текстовых титров: `hook` / `fact` / `cta`.

## Быстрый запуск

Скрипт перед запуском делает Preflight-проверку зависимостей и печатает статус нужных бинарей/пакетов.

Перед первым запуском подтяни локальные шрифты (в репозитории они не хранятся):

```bash
bash scripts/setup_local_assets.sh
```

```bash
python scripts/run_pipeline.py \
  --episode episode_demo \
  --asr-provider faster_whisper_local \
  --hooks-provider ollama_local \
  --render-provider ffmpeg_local \
  --from-scene 0 --to-scene 5
```

## Быстрый процесс для нового ролика

1. Положить файлы в `input/<episode_id>/`.
2. Заполнить `episode_manifest.json` (можно добавить `music`).
3. Выбрать `style_id` (например `serial_reference_style`) и (опционально) добавить `overrides` в манифест.
4. Запустить `scripts/run_pipeline.py` (можно ограничить диапазон сцен `--from-scene/--to-scene`).
5. Проверить `output/<episode_id>/artifacts`:
   - `final.mp4`
   - `alt.mp4`
   - `render_outputs.json`
   - `overrides_template.json`
   - `qc_report.json`
   - `transcript.json`
   - `clip_signatures.json`

Пример `episode_manifest.json`:

```json
{
  "audio": "voiceover.wav",
  "music": "bg_music.mp3",
  "script": "script.txt",
  "visuals": ["slide_01.png", "slide_02.png", "clip_03.mp4"],
  "style_id": "default_style",
  "overrides": [
    {"scene_index": 0, "headline": "ПЕРЕПИСАННЫЙ ХУК"},
    {"scene_index": 2, "visual_ref": "my_custom_slide.png"}
  ]
}
```


## Style library

Подробный разбор по сборке библиотеки стиля из референсов: `docs/STYLE_LIBRARY_SETUP.md`.

### Slot-based templates (rules, not content)

Система строится как `slots + rules`: шаблоны не хранят конкретный текст/маскота, а описывают раскладку слоёв и имена слотов.

- `templates/styles/red.json | blue.json | black.json` — палитры и пары шрифтов (с `size_ratio` для масштабирования под любое разрешение).
- `templates/scenes/hook.json | fact.json | cta.json` — абстрактные сцены со слотами (`headline`, `accent_top`, `visual_ref`, `mascot_action`).
- Контент приходит из сценария/override: например `mascot_action: "duck_teacher"` → `assets/mascots/duck_teacher.png`.
- Для конкретного выпуска можно добавлять дополнительные медиа через `extra_media` в `episode_manifest.json`.


## Про бинарные ассеты

Чтобы избежать конфликтов PR в GitHub UI, тяжелые бинарные ассеты (шрифты/медиа) рекомендуется хранить локально или в отдельном storage, а в git держать манифесты и плейсхолдеры.


## Runtime dependencies

Dependencies are declared in `pyproject.toml` (faster-whisper, ffmpeg-python, pydantic, ollama).


## Remotion path

`remotion_local` теперь при ошибке падает в production fallback на `ffmpeg_local`, а не в текстовый preview.

## Hooks quality

`ollama_local` использует постфильтры (JSON parse + rules refine + anti-repeat) для более стабильных headline.
