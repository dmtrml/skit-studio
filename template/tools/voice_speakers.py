"""Speaker check: was every line read by the right voice? Run after prep.py.
usage: python tools/voice_speakers.py [SKIT_DIR]     (default: the skit folder that holds this tools/)

For every line of timeline.json: median pitch (F0, autocorrelation over voiced 40 ms frames) in voice/voice.wav.
Guy = Puck (higher), Ko = Charon (lower). A line is FLAGGED when its F0 is nearer the other speaker's median
than its own, or when it has < 5 voiced frames (1-word lines: check by ear on the rhythm draft).
Prints one row per line and the gap between the two speaker medians. Puck and Charon are both male voices: skit 2 gap
was only 12.5 Hz (guy 93.8, Ko 81.2) and 1 false flag (L4, Ko dictating «Пишу: …» higher) - a flag means LISTEN to that
line, not re-take."""
import json
import sys
import wave
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

skit = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
tl = json.loads((skit / "timeline.json").read_text(encoding="utf-8"))
with wave.open(str(skit / "voice/voice.wav")) as w:
    sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
if ch > 1:
    x = x.reshape(-1, ch).mean(axis=1)


def f0s(a):
    fl, hop, lo, hi = int(.04 * sr), int(.01 * sr), int(sr / 400), int(sr / 70)
    out = []
    for i in range(0, len(a) - fl, hop):
        f = a[i:i + fl] - a[i:i + fl].mean()
        if np.sqrt((f ** 2).mean()) < 0.01:
            continue
        c = np.correlate(f, f, "full")[fl - 1:]
        if c[0] <= 0:
            continue
        k = lo + int(np.argmax(c[lo:hi]))
        if c[k] / c[0] > 0.5:
            out.append(sr / k)
    return out


rows = []
for L in tl["lines"]:
    v = f0s(x[int(L["start"] * sr):int(L["end"] * sr)])
    rows.append((L["id"], L["speaker"], float(np.median(v)) if v else float("nan"), len(v), L["text"][:40]))
med = {s: float(np.nanmedian([r[2] for r in rows if r[1] == s and r[3] >= 5] or [np.nan])) for s in ("guy", "ko")}
bad = 0
for lid, sp, f, nv, txt in rows:
    other = "ko" if sp == "guy" else "guy"
    flag = nv < 5 or (not np.isnan(f) and abs(f - med[other]) < abs(f - med[sp]))
    bad += flag
    print(f"{lid:>4} {sp:<4} F0 {f:6.1f} Hz  frames {nv:4d}  {'FLAG' if flag else 'ok  '}  {txt}")
print(f"median guy {med['guy']:.1f} Hz, ko {med['ko']:.1f} Hz, gap {med['guy'] - med['ko']:.1f} Hz; flagged {bad}")
