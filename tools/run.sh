#!/usr/bin/env bash
# Run a heavy job (HyperFrames check/snapshot/render, ffmpeg, node with a browser):  bash tools/run.sh <cmd...>
# Default: just runs the command. Weak PC (reboots or freezes on render): set SKIT_THROTTLE=1 -> at most
# SKIT_SLOTS (default 2) heavy jobs at once, a new job starts >= SKIT_STAGGER (default 20) s after the previous start,
# below-normal priority on Windows, `render` gets --workers 2, short pause after. Run renders in the background.
if [ "${SKIT_THROTTLE:-0}" != "1" ]; then exec "$@"; fi
SLOTS="${SKIT_SLOTS:-2}"; GAP="${SKIT_STAGGER:-20}"
B="$HOME/.skit-run.lock"; G="$HOME/.skit-run.start"
args=(); skip=0
for a in "$@"; do
  if [ $skip = 1 ]; then skip=0; continue; fi
  case "$a" in --workers) skip=1; continue;; --workers=*) continue;; esac
  args+=("$a")
done
case " ${args[*]} " in *" render "*) args+=(--workers 2);; esac
stale() { local pid; pid=$(cut -d' ' -f1 "$1/owner" 2>/dev/null); [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; }
for i in $(seq 1 1800); do
  for s in $(seq 1 "$SLOTS"); do
    L="$B.$s"
    if mkdir "$L" 2>/dev/null; then
      echo "$$ $(pwd)" > "$L/owner"
      trap 'rm -rf "$L"' EXIT INT TERM
      until mkdir "$G.gate" 2>/dev/null; do sleep 1; done
      last=$(cat "$G" 2>/dev/null || echo 0); now=$(date +%s)
      [ $((now - last)) -lt "$GAP" ] && sleep $((GAP - (now - last)))
      date +%s > "$G"; rmdir "$G.gate"
      W=$(cat /proc/$$/winpid 2>/dev/null)
      [ -n "$W" ] && powershell -NoProfile -Command "(Get-Process -Id $W).PriorityClass='BelowNormal'" >/dev/null 2>&1
      "${args[@]}"; rc=$?
      sleep 10
      exit $rc
    fi
    stale "$L" && { echo "run.sh: stale lock $L, removing" >&2; rm -rf "$L"; }
  done
  [ -d "$G.gate" ] && [ $(( $(date +%s) - $(stat -c %Y "$G.gate" 2>/dev/null || date +%s) )) -gt 120 ] && rmdir "$G.gate" 2>/dev/null
  [ $((i % 30)) -eq 1 ] && echo "run.sh: all $SLOTS slots busy" >&2
  sleep 2
done
echo "run.sh: slots busy for 60 min, giving up" >&2
exit 3
