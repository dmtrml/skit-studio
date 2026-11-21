"""Music preview on the accepted picture, no re-render (rule C-2026-11-09-mstem).
    python sound/music/preview.py DRAFT.mp4 RAW.wav OUT.mp4     (run through gpu.sh: it calls ffmpeg)
RAW = full-length pre-level music (e.g. music_b_raw.wav from synth.py) -> to_stem (voice-relative levels, ducking)
+ the draft's own audio -> gain to -14 LUFS -> alimiter level=disabled -> mux with -c:v copy."""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SR, N, load, to_stem  # noqa

draft, rawp, out = sys.argv[1:4]
tmp = Path(out).with_suffix('')
da, mixw = f"{tmp}_draft.wav", f"{tmp}_mix.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", draft, "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", da], check=True)
d = load(da)
stem = to_stem(load(rawp)[:N])
n = min(len(d), len(stem))
mix = d[:n] + stem[:n]
sf.write(mixw, mix, SR, subtype="FLOAT")
# measure, then one gain + limiter pass
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", mixw, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(json.loads(m[m.rindex("{"):m.rindex("}") + 1])["input_i"])
g = -14.0 - I
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", draft, "-i", mixw, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", f"volume={g:.2f}dB,alimiter=limit=0.89:level=disabled", "-c:a", "aac", "-b:a", "256k", out], check=True)
print(f"mix {I:.1f} LUFS -> gain {g:+.2f} dB -> {out}")
Path(da).unlink(); Path(mixw).unlink()
