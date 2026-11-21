"""Static checks of the plugin, no network: python tests/run_tests.py  (last line: OK n checks)."""
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
fails: list[str] = []
count = 0
PENDING = ("template/", "props/")  # copied into the plugin at assembly time
TEXT_EXT = {".md", ".py", ".sh", ".mjs", ".json", ".txt", ".js", ".html"}


def check(cond, name):
    global count
    count += 1
    if not cond:
        fails.append(name)
    return bool(cond)


def run(args, env=None, cwd=None, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=cwd, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in TEXT_EXT and not {"__pycache__", "node_modules", "template", "props"} & set(p.relative_to(ROOT).parts):
            yield p


def test_manifest():
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(pj.get("name") == "skit-studio" and re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")), "plugin.json name/version")
    check(len(pj.get("description", "")) > 20 and pj.get("author", {}).get("name"), "plugin.json description/author")
    mp = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    check(mp["plugins"][0]["name"] == "skit-studio" and mp["plugins"][0]["version"] == pj["version"], "marketplace.json matches")
    for name in ("setup", "start", "check"):
        t = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"---\nname: (\S+)\ndescription: (.+)\n---\n", t)
        check(m and m.group(1) == name and len(m.group(2)) > 40, f"skill {name} frontmatter")
    for f in ("README.md", "START-HERE-CLAUDE.md", "LICENSE", "tools/run.sh", "tools/hf_version.txt", "scripts/install.py", "scripts/new_skit.py"):
        check((ROOT / f).is_file(), "exists " + f)
    for f in ("paths.sh", "paths.py", "paths.mjs"):
        check((ROOT / "template-overrides" / "tools" / f).is_file(), "override " + f)


def test_paths_named():
    bad = []
    for sk in (ROOT / "skills").rglob("*.md"):
        t = sk.read_text(encoding="utf-8")
        for tok in re.findall(r"`([^`\n]+)`", t):
            for m in re.findall(r"<plugin>/([\w./-]+)", tok):
                if m.startswith(PENDING) or "<" in m:
                    continue
                if not (ROOT / m.rstrip("/")).exists():
                    bad.append(f"{sk.name}: {m}")
            if re.fullmatch(r"references/[\w./-]+", tok) and not (ROOT / "skills" / "start" / tok).exists():
                bad.append(f"{sk.name}: {tok}")
    check(not bad, "skill paths exist: " + "; ".join(bad))


def test_no_user_paths():
    pats = [re.compile(p, re.I) for p in ("C:[/\\\\]+Users", "/c/Users", "Users[/\\\\]user", "You" + "Tube", "Co" + "Development", "dmtrml/mult")]
    pats = pats[:-1]
    hits = []
    for p in text_files():
        t = p.read_text(encoding="utf-8", errors="replace")
        if p.name == "run_tests.py":
            continue
        for rx in pats:
            if rx.search(t):
                hits.append(f"{p.relative_to(ROOT)}:{rx.pattern}")
    check(not hits, "no absolute user paths: " + ", ".join(hits))


def test_python_tools():
    ok, errs = 0, []
    for p in ROOT.rglob("*.py"):
        if "__pycache__" in p.parts or "template" in p.relative_to(ROOT).parts[:1]:
            continue
        try:
            py_compile.compile(str(p), cfile=str(Path(tempfile.gettempdir()) / 'skit_pc_test.pyc'), doraise=True)
            ok += 1
        except py_compile.PyCompileError as e:
            errs.append(f"{p.name}: {e.msg[:80]}")
    check(ok >= 8 and not errs, "python files compile: " + "; ".join(errs))
    for sh in ("tools/run.sh", "template-overrides/tools/paths.sh"):
        check(run(["bash", "-n", sh], cwd=ROOT)[0] == 0, "bash -n " + sh)
    rc, out, _ = run(["bash", "tools/run.sh", "echo", "hi"], cwd=ROOT)
    check(rc == 0 and out.strip() == "hi", "run.sh plain mode runs the command")
    src = (ROOT / "tools" / "render_ss.py").read_text(encoding="utf-8")
    check("hf_version.txt" in src and "0.9.26" not in src, "render_ss default --hf comes from hf_version.txt")
    check(re.fullmatch(r"\d+\.\d+\.\d+", (ROOT / "tools" / "hf_version.txt").read_text(encoding="utf-8").strip()), "hf_version.txt is a version")


def test_install_and_new_skit():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "home"
        home.mkdir()
        env = dict(os.environ, USERPROFILE=str(home), HOME=str(home), PYTHONIOENCODING="utf-8")
        rc, out, err = run([PY, str(ROOT / "scripts" / "install.py")], env=env)
        check(rc in (0, 1) and ("ГОТОВО" in out or "НЕ ХВАТАЕТ" in out or "МОЖНО НАЧИНАТЬ" in out), "install.py check mode prints a verdict")
        check((home / ".skit-studio" / "config.json").is_file(), "install.py writes config.json in home")
        check("AIza" not in out, "install.py never prints a key")
        # the key file: created by --key-file, read by the check, never printed
        env2 = {k: v for k, v in env.items() if k != "GEMINI_API_KEY"}
        env2["SKIT_NO_OPEN"] = "1"
        kf = home / ".skit-studio" / "gemini-key.txt"
        rc, out, err = run([PY, str(ROOT / "scripts" / "install.py"), "--key-file"], env=env2)
        check(rc == 0 and kf.is_file() and kf.read_text(encoding="utf-8").startswith("#"), "install.py --key-file creates the key file with a comment line")
        kf.write_text(kf.read_text(encoding="utf-8") + "AIzaFAKE-TEST-KEY\n", encoding="utf-8")
        rc, out, err = run([PY, str(ROOT / "scripts" / "install.py"), "--json"], env=env2)
        check("AIza" not in out + err, "install.py never prints a key from the key file")
        if sys.platform != "win32":  # on Windows the check may also find a key in the user's registry
            kf.write_text("# только комментарий\n", encoding="utf-8")
            rc, out2, err = run([PY, str(ROOT / "scripts" / "install.py"), "--json"], env=env2)
            g = [r for r in json.loads(out2) if r["id"] == "gemini"][0]
            check(not g["ok"], "a key file with only a comment is not a key")
        g = [r for r in json.loads(out) if r["id"] == "gemini"][0]
        check(g["ok"], "install.py finds the key in the key file")
        # a plugin copy with a fake template (the real one lands at assembly)
        plug = td / "Плагин"
        for d in ("scripts", "tools"):
            shutil.copytree(ROOT / d, plug / d, ignore=shutil.ignore_patterns("__pycache__"))
        if (ROOT / "template").is_dir():
            shutil.copytree(ROOT / "template", plug / "template")
        else:
            (plug / "template" / "tools").mkdir(parents=True)
            (plug / "template" / "README.md").write_text("шаблон", encoding="utf-8")
        ws = td / "Мои скетчи"
        ws.mkdir()
        rc, out, err = run([PY, str(plug / "scripts" / "new_skit.py"), "Скетч-тест", "--dir", str(ws)], env=env)
        sk = ws / "Скетч-тест"
        check(rc == 0 and sk.is_dir(), "new_skit.py into a Cyrillic folder: " + (err or out)[-120:])
        check((sk / "README.md").is_file() and (sk / "tools" / "plugin_root.txt").read_text(encoding="utf-8").strip() == plug.as_posix(), "new_skit writes template + plugin_root.txt (forward slashes)")
        check((sk / "sound" / "music" / "common.py").is_file(), "new_skit copies music helpers")
        rc2, _, _ = run([PY, str(plug / "scripts" / "new_skit.py"), "Скетч-тест", "--dir", str(ws)], env=env)
        check(rc2 != 0, "new_skit refuses to overwrite")
        # Codex/Git Bash: no CR in any .sh, a backslash plugin path still resolves, .gitattributes pins LF
        crlf = [str(f.relative_to(ROOT)) for f in ROOT.rglob("*.sh") if b"\r" in f.read_bytes()]
        check(not crlf, "no CRLF in .sh: " + ", ".join(crlf[:3]))
        ga = ROOT / ".gitattributes"
        check(ga.is_file() and "*.sh text eol=lf" in ga.read_text(encoding="utf-8"), ".gitattributes keeps .sh LF")
        check((ROOT / ".codex-plugin" / "plugin.json").is_file() and (ROOT / ".agents" / "plugins" / "marketplace.json").is_file(), "Codex manifests present")
        if shutil.which("bash"):
            (sk / "tools" / "plugin_root.txt").write_text(str(plug).replace("/", "\\"), encoding="utf-8")
            rc, out, err = run([shutil.which("bash"), "-c", "source tools/paths.sh && echo $PB"], env={k: v for k, v in env.items() if k != "SKIT_STUDIO_ROOT"}, cwd=sk)
            check(rc == 0 and out.strip().endswith("/tools") and "\\" not in out, "paths.sh accepts a backslash plugin path: " + (err or out)[-120:])
            (sk / "tools" / "plugin_root.txt").write_text(plug.as_posix(), encoding="utf-8")
        # overrides resolve the plugin through plugin_root.txt
        shutil.copy(ROOT / "template-overrides" / "tools" / "paths.py", sk / "tools" / "paths.py")
        rc, out, err = run([PY, "-c", "import sys;sys.path.insert(0,'tools');import paths;print(paths.G.name, paths.PB.name)"], env=env, cwd=sk)
        check(rc == 0 and out.strip() == "run.sh tools", "paths.py finds the plugin: " + (err or out)[-120:])


def test_words_utf8_demo():
    # (3) words.py: indices, total, --lines check, UTF-8 even on a cp1251 console
    with tempfile.TemporaryDirectory() as td:
        wj = Path(td) / "w.words.json"
        words = [{"word": " Привет,", "start": 0.0, "end": 0.4}, {"word": " Ко.", "start": 0.5, "end": 0.8}, {"word": " —", "start": 0.9, "end": 1.0}]
        wj.write_text(json.dumps({"segments": [{"words": words}]}, ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="cp1251")
        r = subprocess.run([PY, str(ROOT / "tools" / "words.py"), str(wj), "--lines", "2,1"], capture_output=True, env=env)
        out = r.stdout.decode("utf-8", errors="replace")
        check(r.returncode == 0 and "total 3 words" in out and "Привет," in out and "OK: counts sum" in out, "words.py prints indexed UTF-8 words and checks counts")
        r = subprocess.run([PY, str(ROOT / "tools" / "words.py"), str(wj), "--lines", "2,2"], capture_output=True, env=env)
        check(r.returncode == 1, "words.py flags a wrong sum")
    # (4) every script that prints reconfigures stdout to UTF-8
    bad = []
    for d in ("tools", "scripts", "template/tools", "template/characters"):
        for p in (ROOT / d).rglob("*.py"):
            t = p.read_text(encoding="utf-8")
            if "print(" in t and "reconfigure" not in t:
                bad.append(str(p.relative_to(ROOT)))
    check(not bad, "UTF-8 stdout in: " + ", ".join(bad))
    # (2) new_skit moves the demo take away (unless --keep-demo); the real template ships the demo files
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        plug = td / "p"
        for d in ("scripts", "tools"):
            shutil.copytree(ROOT / d, plug / d, ignore=shutil.ignore_patterns("__pycache__"))
        (plug / "template" / "voice").mkdir(parents=True)
        for f in ("take1.wav", "take1.words.json", "dialog.txt"):
            (plug / "template" / "voice" / f).write_text("x", encoding="utf-8")
        run([PY, str(plug / "scripts" / "new_skit.py"), "a", "--dir", str(td)])
        run([PY, str(plug / "scripts" / "new_skit.py"), "b", "--dir", str(td), "--keep-demo"])
        check(not (td / "a" / "voice" / "take1.wav").exists() and (td / "a" / "old" / "demo" / "voice" / "take1.words.json").exists() and (td / "a" / "voice" / "dialog.txt").exists(), "new_skit moves demo take to old/demo")
        check((td / "b" / "voice" / "take1.wav").exists(), "new_skit --keep-demo keeps it")
    sk = (ROOT / "skills" / "start" / "SKILL.md").read_text(encoding="utf-8")
    check("демо" in sk and "prep.py" in sk and "words.py" in sk and "Kore" in sk and "SKIT_STUDIO_ROOT" in sk, "start skill documents demo files, words.py, voices, plugin root")


def test_onboarding():
    ex = ROOT / "examples" / "ko-skit-example.mp4"
    check(ex.is_file() and ex.stat().st_size <= 10 * 1024 * 1024, "example video exists and <= 10 MB")
    sk = (ROOT / "skills" / "start" / "SKILL.md").read_text(encoding="utf-8")
    need = ["AskUserQuestion", "Есть своя", "Есть тема — предложи 3", "Удиви меня", "Парень по умолчанию", "Свой по картинке",
            "Опишу словами", "Ко как есть", "Ко другого цвета/формы", "хочу скетч", "сделай скетч", "сними ролик с Ко", "config.json"]
    miss = [n for n in need if n not in sk]
    check(not miss, "start skill onboarding block: missing " + ", ".join(miss))
    check(all(len(x) <= 40 for x in ("Есть тема — предложи 3", "Ко другого цвета/формы")), "option labels short")
    rd = (ROOT / "README.md").read_text(encoding="utf-8")
    check("/skit-studio:start" in rd and "хочу скетч" in rd, "README names the entry line")
    pj = (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    check("/skit-studio:start" in pj, "plugin.json names the entry line")


def test_words_branch_and_hero_sheet():
    sk = (ROOT / "skills" / "start" / "SKILL.md").read_text(encoding="utf-8")
    ch = (ROOT / "skills" / "start" / "references" / "characters.md").read_text(encoding="utf-8")
    # (1) the words branch: guide, file name/location, use.py command, honest list of what is not supported
    need = ["references/characters.md", "characters/<имя>.json", "python characters/use.py <имя>.json", "честно"]
    miss = [n for n in need if n not in sk]
    check(not miss, "words branch names guide/passport file/use.py: missing " + ", ".join(miss))
    check(all(w in ch for w in ("mustache", "age", "vest_over_shirt", "cannot do")), "characters guide lists mustache/age/vest and the limits table")
    check((ROOT / "template" / "characters" / "old_man.json").is_file() or not (ROOT / "template").is_dir(), "old_man passport exists")
    # (3) hero sheet without demo subtitles
    ss = (ROOT / "template" / "tools" / "snap_sheet.sh")
    if ss.exists():
        s = ss.read_text(encoding="utf-8")
        check("hero" in s and "nocap" in s and "SKIT_NOCAP" in s, "snap_sheet.sh has hero mode with captions hidden")
        check("CUES.nocap" in (ROOT / "template" / "code" / "index.html").read_text(encoding="utf-8"), "index.html honours CUES.nocap")
    check("snap_sheet.sh hero" in sk and "субтитры скрыты" in sk, "start skill uses the hero sheet with captions hidden")
    st = (ROOT / "template" / "voice" / "style.txt")
    if st.exists():
        x = st.read_text(encoding="utf-8")
        check("ЗАПОЛНИ" in x and "знакомств" not in x and "молодой парень" not in x, "style.txt is a neutral template")
    check("Algenib" in sk and "Gacrux" in sk and "возраст" in sk, "voices by gender and age listed")


def main():
    for t in (test_manifest, test_paths_named, test_no_user_paths, test_python_tools, test_install_and_new_skit, test_words_utf8_demo, test_onboarding, test_words_branch_and_hero_sheet):
        try:
            t()
        except Exception as e:  # a crashed test is a failed test
            check(False, f"{t.__name__} crashed: {e!r}"[:200])
    for f in fails:
        print("FAIL", f)
    print(f"{'OK' if not fails else 'FAILED'} {count} checks" + (f", {len(fails)} failed" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
