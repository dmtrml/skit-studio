"""Find the skit-studio plugin and the skit folder.

    from paths import SKIT, ROOT, PLUGIN, G, PB, PW     # SKIT = the skit folder (parent of tools/); ROOT = SKIT
Plugin lookup: env SKIT_STUDIO_ROOT -> tools/plugin_root.txt (written by new_skit.py) -> ~/.skit-studio/config.json (written by install.py).
"""
import json
import os
from pathlib import Path

SKIT = Path(__file__).resolve().parents[1]
ROOT = SKIT


def _plugin():
    if os.environ.get("SKIT_STUDIO_ROOT"):
        return Path(os.environ["SKIT_STUDIO_ROOT"])
    f = SKIT / "tools" / "plugin_root.txt"
    if f.exists():
        return Path(f.read_text(encoding="utf-8").strip())
    c = Path.home() / ".skit-studio" / "config.json"
    if c.exists():
        return Path(json.loads(c.read_text(encoding="utf-8"))["plugin"])
    return None


PLUGIN = _plugin()
if PLUGIN is None or not (PLUGIN / "tools" / "run.sh").exists():
    raise SystemExit("paths.py: skit-studio plugin not found (run /skit-studio:setup)")
G = PLUGIN / "tools" / "run.sh"
PB = PLUGIN / "tools"
PW = Path(os.environ.get("SKIT_PLAYWRIGHT", Path.home() / ".skit-studio" / "node_modules" / "playwright" / "index.mjs"))
