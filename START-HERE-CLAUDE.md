# Для Claude: человек дал ссылку на этот репозиторий

Человек хочет сделать скетч с ИИ-помощником Ко. Говори по-русски, коротко, без жаргона. Спрашивай только то, что решает он: разрешения на установку, тему, выбор шутки. Остальное делай сам.

Рабочая папка `<ws>` — папка, открытая в Claude Code. Платформа: Windows проверена; macOS и Linux — по аналогии, скажи об этом честно.

## 1. Скачать репозиторий

Положи его в постоянное место (не в `<ws>`): `<repo>` = `~/.skit-studio/plugin` (Windows: `%USERPROFILE%\.skit-studio\plugin`). Если папка есть — обнови, не создавай вторую.

- Есть `git` → `git clone https://github.com/dmtrml/skit-studio "<repo>"`.
- Нет `git` → PowerShell: `Invoke-WebRequest https://github.com/dmtrml/skit-studio/archive/refs/heads/main.zip -OutFile "$env:TEMP\skit.zip"; Expand-Archive "$env:TEMP\skit.zip" "$env:TEMP\skit" -Force` и перенеси содержимое `skit-studio-main` в `<repo>`.

Это небольшая папка (несколько МБ), отдельное разрешение не нужно: человек сам прислал ссылку.

## 2. Подключить плагин

Скажи одной фразой, что подключаешь плагин. Найди `claude` (`where claude`; в приложении Claude его часто нет в PATH — ищи `%LOCALAPPDATA%\Claude-Data\*\claude-code\*\*\claude.exe`). Затем `claude plugin marketplace add "<repo>"` и `claude plugin install skit-studio@skit-studio`. Не вышло — оставь человеку один шаг: в новой сессии `/plugin marketplace add dmtrml/skit-studio`, `/plugin install skit-studio@skit-studio`. Работу не останавливай: плагин заработает в **новых** сессиях, в этой читай файлы из `<repo>`.

## 3. Установка

Прочитай `<repo>/skills/setup/SKILL.md` и выполни (`<plugin>` = `<repo>`). Перед установкой — **один** вопрос со списком и размерами. Если Windows спросит «Разрешить изменения?», заранее скажи нажать «Да».

## 4. Проверка

`python "<repo>/scripts/install.py"` — покажи вывод как есть. `ГОТОВО` → шаг 5. «НЕТ» только у `playwright` и `hyperframes` не блокирует шаги 1–8 скетча (они нужны на шаге 9 / прогреваются сами). Иначе почини по `setup/SKILL.md`. Если программа «не видна» сразу после установки — попроси перезапустить приложение Claude и вставить тот же промпт.

## 5. Начать скетч

Прочитай `<repo>/skills/start/SKILL.md` и веди с шага 1 (таблица шуток). В конце сессии скажи, что продолжать можно командой `/skit-studio:start` в новой сессии этой же папки.
