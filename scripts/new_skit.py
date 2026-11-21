"""Новый скетч: python new_skit.py <имя> [--dir ПАПКА]

Копирует template/ плагина в <ПАПКА>/<имя>/ (по умолчанию ПАПКА = текущая; кириллица в именах работает),
кладёт tools/plugin_root.txt (где плагин) и копирует музыкальные помощники tools/music/ в sound/music/.
Не перезаписывает существующую папку.
"""
import argparse
import shutil
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
DEMO_INPUTS = ("voice/take1.wav", "voice/take1.words.json")


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Создать папку нового скетча из шаблона")
    ap.add_argument("name")
    ap.add_argument("--dir", default=".", help="где создать (по умолчанию текущая папка)")
    ap.add_argument("--keep-demo", action="store_true", help="не убирать демо-озвучку шаблона (voice/take1.wav и take1.words.json)")
    a = ap.parse_args(argv)
    src = PLUGIN / "template"
    if not src.is_dir():
        sys.exit("нет template/ в плагине: " + str(src))
    dst = Path(a.dir).expanduser().resolve() / a.name
    if dst.exists():
        sys.exit("папка уже есть, не трогаю: " + str(dst))
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules"))
    (dst / "tools").mkdir(exist_ok=True)
    (dst / "tools" / "plugin_root.txt").write_text(PLUGIN.as_posix(), encoding="utf-8")  # forward slashes: Git Bash reads this path
    mus = PLUGIN / "tools" / "music"
    if mus.is_dir():
        shutil.copytree(mus, dst / "sound" / "music", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Mixkit sounds are not shipped with the plugin (licence): install.py downloads them to ~/.skit-studio/sfx/
    sfx_home = Path.home() / ".skit-studio" / "sfx"
    sfx_dst = dst / "sound" / "src"
    sfx_dst.mkdir(parents=True, exist_ok=True)
    got = sorted(sfx_home.glob("*.mp3")) if sfx_home.is_dir() else []
    for f in got:
        shutil.copy2(f, sfx_dst / f.name)
    moved = []
    if not a.keep_demo:  # the template ships a 3-line demo take; move it away so no tool silently uses it
        for rel in DEMO_INPUTS:
            f = dst / rel
            if f.exists():
                (dst / "old" / "demo" / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(dst / "old" / "demo" / rel))
                moved.append(rel)
    print("создано:", dst)
    if moved:
        print("демо-дубль убран в old/demo/:", ", ".join(moved), "(остальное в шаблоне — демо-данные, см. skills/start, шаг 2)")
    if not got:
        print('звуков Mixkit нет: python "' + (PLUGIN / "scripts" / "install.py").as_posix() + '" --install --only sfx, потом скопируйте ~/.skit-studio/sfx/*.mp3 в sound/src/')
    print("дальше: cd в эту папку; source tools/paths.sh; шаг 1 — таблица сценария (skills/start)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
