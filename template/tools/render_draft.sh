#!/usr/bin/env bash
# Draft render + snapshots at 0 and duration/2 + postcheck. Run in the background (gpu.sh queues for a slot):
#   bash tools/render_draft.sh NAME [WORKERS=2]        -> ../NAME.mp4 (next to tools/), snaps/NAME-post/, snaps/NAME-sheet.jpg
# If postcheck reports a diff > 3 (2-worker seek bug) it re-renders once with --workers 1.
. "$(dirname "$0")/paths.sh"
NAME="${1:?usage: render_draft.sh NAME [WORKERS]}"; W="${2:-2}"
cd "$SKIT/code"
mid=$(python -c "import json;print(json.load(open('../timeline.json',encoding='utf-8'))['frames']//2/30)")
for pass in 1 2; do
  S=$(date +%s)
  bash "$G" npx --yes hyperframes@0.9.31 render --quality draft --workers "$W" --output "../$NAME.mp4" 2>&1 | tail -3
  echo "RENDER_SECONDS $(( $(date +%s) - S )) (workers $W)"
  rm -rf snapshots "../snaps/$NAME-post"; mkdir -p "../snaps/$NAME-post"
  for k in 1 2 3; do
    bash "$G" npx --yes hyperframes@0.9.31 snapshot --describe false --no-end --output snapshots --at "0,$mid" >/dev/null 2>&1
    [ "$(ls snapshots/frame-*.png 2>/dev/null | wc -l)" -ge 2 ] && break
  done
  cp snapshots/frame-0[01]-at-*.png "../snaps/$NAME-post/"
  rm -rf snapshots
  cd "$SKIT" && python tools/postcheck.py "$NAME.mp4" "snaps/$NAME-post" "snaps/$NAME-sheet.jpg"; rc=$?
  [ $rc -eq 0 ] && break
  [ "$W" -gt 1 ] || { echo "already 1 worker: compare the frame with the snapshot by eye (HOWTO §4)"; break; }   # skit 3: 1-worker re-render repeated the same diff
  [ "$pass" = 1 ] && { W=1; cd "$SKIT/code"; echo "re-render with --workers 1"; }
done
