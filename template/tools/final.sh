#!/usr/bin/env bash
# Final: 4K supersampled picture (render_ss, 1080x1920 out) + the approved preview's audio as is, then checks. Run in the background.
#   bash tools/final.sh NAME AUDIO_SOURCE ACCEPTED_DRAFT
#     NAME            -> NAME-video.mp4 (picture only) and NAME.mp4 (final), next to tools/
#     AUDIO_SOURCE    approved preview mp4 whose audio track is used with -c copy (the track the author heard)
#     ACCEPTED_DRAFT  the approved draft mp4 for render_diff (worst cell ~6-8 is 4K smoothing of text/glow edges)
set -e
. "$(dirname "$0")/paths.sh"
NAME="${1:?NAME}"; AUDIO="${2:?AUDIO_SOURCE}"; DRAFT="${3:?ACCEPTED_DRAFT}"
cd "$SKIT"
date +%H:%M
bash "$G" python "$PB/render_ss.py" code "$NAME-video.mp4" --portrait --hf 0.9.31 --workers 2 | tail -2
bash "$G" ffmpeg -v error -y -i "$NAME-video.mp4" -i "$AUDIO" -map 0:v -map 1:a -c copy -movflags +faststart "$NAME.mp4"
bash "$G" ffmpeg -hide_banner -nostats -i "$NAME.mp4" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):"
SNAP="snaps/$(basename "$DRAFT" .mp4)-post"   # snaps of the ACCEPTED draft (the newest dir may be another render)
[ -d "$SNAP" ] || SNAP=$(ls -td snaps/*-post 2>/dev/null | head -1)
[ -n "$SNAP" ] && python tools/postcheck.py "$NAME.mp4" "$SNAP" "snaps/$NAME-sheet.jpg" | tail -5
# render_diff exits 1 on any cell > 6 (normal for 4K glow/text edges): judge by the plugin's norm here, not by `| tail`.
bash "$G" python "$PB/render_diff.py" "$DRAFT" "$NAME.mp4" > "snaps/$NAME-diff.txt" || true
tail -14 "snaps/$NAME-diff.txt"
WORST=$(grep -oE 'worst +[0-9.]+' "snaps/$NAME-diff.txt" | awk '{if ($2 > m) m = $2} END {print m + 0}')
if grep -q '^unexpected:' "snaps/$NAME-diff.txt" && awk -v w="$WORST" 'BEGIN {exit !(w <= 8)}'; then
  echo "final.sh: render_diff worst $WORST <= 8 -> OK if every cell > 6 is subtitle text or a glow edge (see the ranges above)"
else
  echo "final.sh: FAIL render_diff worst ${WORST:-?} > 8 (or no result) -> fix before showing (snaps/$NAME-diff.txt)" >&2; exit 1
fi
date +%H:%M
