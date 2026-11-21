# source this: exports SKIT (skit folder), PLUGIN (skit-studio plugin folder), G (run.sh), PB (plugin tools/), ROOT (=SKIT)
SKIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="${SKIT_STUDIO_ROOT:-}"
[ -z "$PLUGIN" ] && [ -f "$SKIT/tools/plugin_root.txt" ] && PLUGIN="$(tr -d '\r\n' < "$SKIT/tools/plugin_root.txt")"
[ -z "$PLUGIN" ] && [ -f "$HOME/.skit-studio/config.json" ] && PLUGIN="$(python -c "import json,os;print(json.load(open(os.path.expanduser('~/.skit-studio/config.json'),encoding='utf-8')).get('plugin',''))")"
PLUGIN="${PLUGIN//\\//}"   # C:\a\b -> C:/a/b (old plugin_root.txt, Windows env)
if [ -z "$PLUGIN" ] || [ ! -f "$PLUGIN/tools/run.sh" ]; then echo "paths.sh: skit-studio plugin not found (run /skit-studio:setup)" >&2; return 1 2>/dev/null || exit 1; fi
ROOT="$SKIT"; G="$PLUGIN/tools/run.sh"; PB="$PLUGIN/tools"
export SKIT ROOT PLUGIN G PB
