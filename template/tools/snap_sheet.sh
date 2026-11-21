#!/usr/bin/env bash
# Snapshots at given times -> one labelled contact sheet (tiles 270x480).
#   bash tools/snap_sheet.sh mid                 middle of every shot (from timeline.json)
#   bash tools/snap_sheet.sh 2,6,13.5 [OUT.jpg]  explicit times (comma list)
#   bash tools/snap_sheet.sh hero [OUT.jpg]      the hero sheet: middle of the first A shot and the first B shot, CAPTIONS HIDDEN
#                                                (the template's demo subtitles/plan are never shown as if they were the person's)
# SKIT_NOCAP=1 hides the captions in any mode (snapshots only; cues.js is restored after).
# Output: snaps/sheet.jpg (default); PNGs stay in code/snapshots/. Runs through gpu.sh (slot + start gate), retries up to 3x.
set -e
. "$(dirname "$0")/paths.sh"
AT="${1:-mid}"; OUT="${2:-$SKIT/snaps/sheet.jpg}"
case "$OUT" in /*|?:*) ;; *) OUT="$PWD/$OUT";; esac; mkdir -p "$(dirname "$OUT")"   # relative OUT = from the caller's dir
if [ "$AT" = "hero" ]; then
  SKIT_NOCAP=1
  AT=$(python -c "import json,sys;t=json.load(open(sys.argv[1],encoding='utf-8'));m=lambda c:next((s for s in t['shots'] if s['cam']==c),None);print(','.join(f\"{(s['start']+s['end'])/2:.2f}\" for s in (m('A'),m('B')) if s))" "$SKIT/timeline.json")
  [ "$OUT" = "$SKIT/snaps/sheet.jpg" ] && OUT="$SKIT/snaps/hero.jpg"
fi
if [ "${SKIT_NOCAP:-0}" = "1" ]; then
  cp "$SKIT/code/cues.js" "$SKIT/code/cues.js.bak"; trap 'mv -f "$SKIT/code/cues.js.bak" "$SKIT/code/cues.js"' EXIT
  echo 'window.CUES.nocap=true;' >> "$SKIT/code/cues.js"
fi
if [ "$AT" = "mid" ]; then
  AT=$(python -c "import json,sys;t=json.load(open(sys.argv[1],encoding='utf-8'));print(','.join(f\"{(s['start']+s['end'])/2:.2f}\".rstrip('0').rstrip('.') for s in t['shots']))" "$SKIT/timeline.json")
fi
N=$(echo "$AT" | tr ',' '\n' | wc -l)
mkdir -p "$SKIT/snaps"; cd "$SKIT/code"
for k in 1 2 3; do
  rm -rf snapshots
  bash "$G" npx --yes hyperframes@0.9.31 snapshot --describe false --no-end --output snapshots --at "$AT" >/dev/null 2>&1 || true
  [ "$(ls snapshots/frame-*.png 2>/dev/null | wc -l)" -ge "$N" ] && break
done
python "$SKIT/tools/sheet_shots.py" snapshots "$OUT"
