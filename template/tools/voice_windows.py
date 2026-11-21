"""Voice-window comparison. usage: python tools/voice_windows.py RENDER.mp4
For every line window of timeline.json: peak/RMS (dBFS) of voice.wav alone, of the NEW mix (code/assets voice + sfx_bed)
and of the audio track of RENDER (the earlier render, e.g. the rhythm draft). Voice is untouched if voice.wav is
byte-identical to code/assets/voice.wav and (new mix - voice) differs from (render - voice) only by the bed."""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from paths import SKIT as ROOT
SR = 48000


def dec(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def st(x):
    return (20 * np.log10(max(np.max(np.abs(x)), 1e-9)), 20 * np.log10(max(np.sqrt(np.mean(x ** 2)), 1e-9)))


tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
v = dec(ROOT / "code/assets/voice.wav")
b = dec(ROOT / "code/assets/sfx_bed.wav")
n = min(len(v), len(b))
mix = v[:n] + b[:n]
ren = dec(sys.argv[1])
h = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()
print("voice.wav identical to code/assets/voice.wav:", h(ROOT / "voice/voice.wav") == h(ROOT / "code/assets/voice.wav"))
print(f"{'line':<5}{'voice pk/rms':>16}{'new mix pk/rms':>18}{'render pk/rms':>18}{'d_rms mix-render':>18}")
worst = 0
for ln in tl["lines"]:
    a, e = int(ln["start"] * SR), int(ln["end"] * SR)
    sv, sm, sr_ = st(v[a:e]), st(mix[a:e]), st(ren[a:e])
    worst = max(worst, abs(sm[1] - sr_[1]))
    print(f"{ln['id']:<5}{sv[0]:>8.1f}/{sv[1]:<7.1f}{sm[0]:>10.1f}/{sm[1]:<7.1f}{sr_[0]:>10.1f}/{sr_[1]:<7.1f}{sm[1] - sr_[1]:>14.2f}")
print(f"max |RMS diff| new mix vs render over line windows: {worst:.2f} dB")
