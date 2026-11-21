# Шаблон скетча с Ко

Чистая папка нового скетча в стиле «Плюс один»: комната, парень, Ко, свет, камеры А/Б/В, субтитры. Реквизит и вставки (телефон, чат, попкорн, редактор) подключаются из `../props/` (контракт и инструкции — `../props/README.md`). В папке демо: 3 реплики, 3 кадра, 10,7 с.

Новый скетч создаёт `python <plugin>/scripts/new_skit.py <имя>` — копия этой папки; дальше работать там. Скрипты сами находят корень репозитория (`tools/paths.*`), путей `../../..` нет.

## Файлы

- `voice/dialog.txt`, `voice/style.txt` — пример текста и указаний для Gemini TTS (демо-текст про парня и знакомства; **замени целиком**: `style.txt` — шаблон с метками {ЗАПОЛНИ: …}; голос героя выбирай по полу и возрасту — skills/start, шаг 3; Ko = Charon).
- `voice/take1.wav` + `take1.words.json` — дубль озвучки и слова Whisper (здесь пример из 3 реплик; свой дубль заменяет оба файла).
- `tools/prep.py` — дубль → `voice/voice.wav` с паузами, `timeline.json`, `voice/envelope.json`, `code/data.js`. Таблицы `LINES`, `SHOTS`, `KO`, `EVENTS` — наверху файла (формат в docstring; пример скетча 2 — в комментариях).
- `cues.src.json` → `tools/cues.py` → `cues.json`, `code/cues.js`: жесты, настроения, взгляд, печать, звуки. Время — от реплик («L3.s+0.2»), поэтому правка пауз ничего не ломает. Описание всех ключей — в поле `note`.
- `sound/mix.py` — комната, клавиши, `enter`, список `sfx` из cues → `sound/sfx_bed.wav` и `code/assets/sfx_bed.wav`. Музыки здесь нет. `sound/src/` + `LICENSES.md` — звуки Mixkit.
- `code/` — HyperFrames 0.9.31 + Three.js: `index.html` (сцена, персонажи, жесты, камеры, субтитры), `look3.js` (свет и материалы), `atmo.js` (пылинки, лучи), `look.js`, `data.js`/`cues.js` (генерируются), `assets/`. Точка подключения реквизита и вставок — комментарий `// PROPS / INSERTS` в `index.html`: по строке `import './props/x.js';` на файл.
- `tools/snap_sheet.sh` — снимки в нужные моменты (`mid` = середина каждого кадра; `hero` = лист героя: общий план A и крупный B со СКРЫТЫМИ субтитрами) → один лист. `render_draft.sh` — черновой рендер + проверка. `final.sh` — финал 4K → 1080 со звуком утверждённого превью.
- Проверки: `voice_speakers.py` (кто читал реплику — по высоте голоса; флаг = послушать), `postcheck.py`, `arm_sweep.mjs` (руки не входят в тело), `gesture_frame.mjs` (жесты в кадре), `hand_boxes.mjs` + `hand_luma.py`, `face_luma.py`, `focus_measure.mjs`, `voice_windows.py`.

## Порядок работы

1. Озвучка: `voice/dialog.txt` → Gemini TTS → `voice/take1.wav`; Whisper → `take1.words.json`.
2. Править таблицы в `tools/prep.py` → `python tools/prep.py` (печатает кадры и реплики; `data-duration` в `index.html` обновляется сам).
3. Подключить нужный реквизит (`../props/README.md`), править `cues.src.json` → `python tools/cues.py`.
4. `python sound/mix.py`.
5. Проверка: `cd code && bash $G npx --yes hyperframes@0.9.31 check`, где `$G` задаёт `source tools/paths.sh` (обычный запуск; `SKIT_THROTTLE=1` — ограничитель для слабых ПК); лист: `bash tools/snap_sheet.sh mid`.
6. Черновик: `bash tools/render_draft.sh NAME` (в фоне). Показывать автору только после просмотра кадров и `postcheck`.
7. Финал: `bash tools/final.sh NAME ПРЕВЬЮ.mp4 ПРИНЯТЫЙ_ЧЕРНОВИК.mp4`.

Всё тяжёлое (check, snapshot, render, ffmpeg) — только через `gpu.sh` (ПК перезагружается на резких скачках нагрузки).
