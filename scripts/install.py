"""Скетч-студия: проверка и установка.

    python install.py              только проверка (ничего не ставит), печатает OK / НЕТ на каждую вещь
    python install.py --install    ставит недостающее (вызывать после «да» человека)
    python install.py --install --only sfx,node,ffmpeg,pip,playwright,hyperframes   только перечисленное
    python install.py --json       проверка в JSON

Что нужно: Python 3.10+, Node.js 18+, ffmpeg, пакеты Python (faster-whisper, numpy, pillow, soundfile, scipy),
playwright (в ~/.skit-studio/node_modules, для инструментов проверки кадров), HyperFrames (прогрев npx),
ключ GEMINI_API_KEY (голос), звуки Mixkit (скачиваются в ~/.skit-studio/sfx/: их лицензия не разрешает
класть файлы в плагин). Ключ никогда не печатается. Пишет ~/.skit-studio/config.json.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
HOME = Path.home() / ".skit-studio"
PIP_PKGS = {"faster-whisper": "faster_whisper", "numpy": "numpy", "pillow": "PIL", "soundfile": "soundfile", "scipy": "scipy"}
WIN = platform.system() == "Windows"
MAC = platform.system() == "Darwin"


def hf_pin():
    f = PLUGIN / "tools" / "hf_version.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else "latest"


def run(cmd, timeout=900, cwd=None, shell=False):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=cwd, shell=shell)
        return r.returncode, ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)


def item(id_, ok, detail, fix=""):
    return {"id": id_, "ok": bool(ok), "detail": detail, "fix": fix}


def c_python():
    v = sys.version_info
    return item("python", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}", "поставьте Python 3.10+ с python.org")


def c_node():
    n = shutil.which("node")
    if not n:
        return item("node", False, "не найден", "winget install OpenJS.NodeJS.LTS" if WIN else "brew install node" if MAC else "поставьте Node.js 18+ (nodejs.org)")
    r = run([n, "--version"], 15)
    m = re.search(r"v(\d+)\.", r[1] if r else "")
    ok = bool(m) and int(m.group(1)) >= 18
    return item("node", ok, (r[1].strip() if r else "?"), "" if ok else "нужен Node.js 18 или новее")


def c_ffmpeg():
    ok = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    return item("ffmpeg", ok, "найден" if ok else "не найден", "winget install Gyan.FFmpeg" if WIN else "brew install ffmpeg" if MAC else "apt install ffmpeg")


def missing_pip():
    code = "import importlib.util,sys;print(' '.join(n for n,m in %r.items() if importlib.util.find_spec(m) is None))" % PIP_PKGS
    r = run([sys.executable, "-c", code], 30)
    return (r[1].split() if r and r[0] == 0 else list(PIP_PKGS))


def c_pip():
    miss = missing_pip()
    return item("pip", not miss, "все пакеты есть" if not miss else "нет: " + ", ".join(miss), "pip install " + " ".join(miss) if miss else "")


def git_bash():
    """Git Bash (not WSL). On Windows a bare `bash` from PowerShell (Codex, plain console) may be C:\\Windows\\System32\\bash.exe = WSL."""
    if not WIN:
        return shutil.which("bash")
    cands = []
    g = shutil.which("git")
    if g:
        root = Path(g).resolve().parent.parent  # ...\Git\cmd\git.exe -> ...\Git
        cands += [root / "bin" / "bash.exe", root.parent / "bin" / "bash.exe"]
    for env in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            cands += [Path(base) / "Git" / "bin" / "bash.exe", Path(base) / "Programs" / "Git" / "bin" / "bash.exe"]
    return next((str(c) for c in cands if c.exists()), None)


def c_bash():
    b = git_bash()
    fix = "winget install Git.Git" if WIN else "поставьте bash"
    return item("bash", bool(b), Path(b).as_posix() if b else "не найден", fix)


def c_playwright():
    env = os.environ.get("SKIT_PLAYWRIGHT")
    if env and Path(env).exists():
        return item("playwright", True, f"SKIT_PLAYWRIGHT={env}")
    ok = (HOME / "node_modules" / "playwright" / "index.mjs").exists()
    return item("playwright", ok, str(HOME / "node_modules") if ok else "не установлен", "python install.py --install --only playwright")


def c_hyperframes():
    cfg = HOME / "config.json"
    ok = cfg.exists() and json.loads(cfg.read_text(encoding="utf-8")).get("hyperframes") == hf_pin()
    return item("hyperframes", ok, f"npx hyperframes@{hf_pin()} прогрет" if ok else "ещё не прогревался", "python install.py --install --only hyperframes")


def gemini_key_set():
    if os.environ.get("GEMINI_API_KEY"):
        return True
    if WIN:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                return bool(winreg.QueryValueEx(k, "GEMINI_API_KEY")[0])
        except OSError:
            return False
    return False


def c_gemini():
    ok = gemini_key_set()
    how = "ключ бесплатно: aistudio.google.com/apikey (вход аккаунтом Google, «Create API key»); положите в переменную среды GEMINI_API_KEY"
    return item("gemini", ok, "ключ найден (не показываю)" if ok else "ключа нет", "" if ok else how)


SFX_DIR = HOME / "sfx"


def sfx_sources():
    f = PLUGIN / "template" / "sound" / "sfx_sources.json"
    return json.loads(f.read_text(encoding="utf-8"))["files"] if f.exists() else {}


def c_sfx():
    src = sfx_sources()
    miss = [n for n in src if not (SFX_DIR / n).is_file()]
    return item("sfx", not miss, f"{len(src) - len(miss)} из {len(src)} звуков" if src else "нет списка звуков",
                "" if not miss else "python install.py --install --only sfx (скачает с mixkit.co)")


CHECKS = [c_python, c_node, c_ffmpeg, c_bash, c_pip, c_playwright, c_hyperframes, c_gemini, c_sfx]


def inst_node():
    if shutil.which("winget") and WIN:
        return run(["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS", "--accept-package-agreements", "--accept-source-agreements"])
    if MAC and shutil.which("brew"):
        return run(["brew", "install", "node"])
    return None, "поставьте Node.js вручную: nodejs.org"


def inst_ffmpeg():
    if WIN and shutil.which("winget"):
        return run(["winget", "install", "-e", "--id", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements"])
    if MAC and shutil.which("brew"):
        return run(["brew", "install", "ffmpeg"])
    return None, "поставьте ffmpeg вручную (ffmpeg.org)"


def inst_pip():
    miss = missing_pip()
    return run([sys.executable, "-m", "pip", "install", *miss]) if miss else (0, "ok")


def inst_playwright():
    npm = shutil.which("npm")
    if not npm:
        return None, "нет npm (сначала Node.js, потом перезапустите приложение)"
    HOME.mkdir(parents=True, exist_ok=True)
    if not (HOME / "package.json").exists():
        (HOME / "package.json").write_text('{"name":"skit-studio-deps","private":true,"type":"module"}\n', encoding="utf-8")
    r = run([npm, "install", "playwright", "--no-audit", "--no-fund"], cwd=HOME, shell=WIN)
    if r[0] != 0:
        return r
    return run(["npx", "--yes", "playwright", "install", "chromium"], cwd=HOME, shell=WIN)


def inst_hyperframes():
    r = run(["npx", "--yes", f"hyperframes@{hf_pin()}", "--help"], 600, shell=WIN)
    if r[0] == 0:
        cfg = read_cfg()
        cfg["hyperframes"] = hf_pin()
        write_cfg(cfg)
    return r


def inst_sfx():
    import urllib.request
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    bad = []
    for name, url in sfx_sources().items():
        dst = SFX_DIR / name
        if dst.is_file() and dst.stat().st_size > 0:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (skit-studio installer)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 1000:
                raise OSError("слишком короткий ответ")
            tmp = dst.with_suffix(".part")
            tmp.write_bytes(data)
            tmp.replace(dst)
        except OSError as e:
            bad.append(f"{name}: {e}")
    return (0, "ok") if not bad else (1, "; ".join(bad))


INSTALLERS = {"sfx": inst_sfx, "node": inst_node, "ffmpeg": inst_ffmpeg, "pip": inst_pip, "playwright": inst_playwright, "hyperframes": inst_hyperframes}


def read_cfg():
    f = HOME / "config.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def write_cfg(cfg):
    HOME.mkdir(parents=True, exist_ok=True)
    cfg["plugin"] = PLUGIN.as_posix()
    b = git_bash()
    if b:
        cfg["bash"] = Path(b).as_posix()  # run every .sh through this one (Codex/PowerShell: never a bare `bash`)
    (HOME / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Проверка и установка Скетч-студии")
    ap.add_argument("--install", action="store_true", help="поставить недостающее")
    ap.add_argument("--only", help="через запятую: " + ",".join(INSTALLERS))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    write_cfg(read_cfg())
    if a.install:
        want = a.only.split(",") if a.only else list(INSTALLERS)
        for name in want:
            if name not in INSTALLERS:
                print("неизвестный пункт:", name)
                continue
            print(f"ставлю {name}…", flush=True)
            r = INSTALLERS[name]()
            print("  " + ("готово" if r and r[0] == 0 else "не вышло: " + (r[1][-300:] if r else "?")), flush=True)
    res = [c() for c in CHECKS]
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(f"{'OK ' if r['ok'] else 'НЕТ'} {r['id']:<12} {r['detail']}" + (f"  → {r['fix']}" if not r["ok"] and r["fix"] else ""))
        bad = [r for r in res if not r["ok"]]
        if not bad:
            print("ГОТОВО")
        elif all(r["id"] in ("playwright", "hyperframes", "sfx") for r in bad):
            print("МОЖНО НАЧИНАТЬ: " + ", ".join(r["id"] for r in bad) + " — не блокируют шаги 1–8 (playwright нужен на шаге 9, hyperframes прогреется сам, звуки sfx нужны к сборке звука)")
        else:
            print("НЕ ХВАТАЕТ: " + ", ".join(r["id"] for r in bad))
    return 0 if all(r["ok"] or r["id"] in ("playwright", "hyperframes", "sfx") for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
