"""Shared helpers for the Phase M music variants (numpy only + soundfile/scipy)."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
DUR = TL["duration"]
N = int(round(DUR * SR))
LINES = {l["id"]: l for l in TL["lines"]}
T_START = LINES["L1"]["start"] - 0.4        # theme enters
T_STOP = LINES["L17"]["end"] + 0.05         # tape-stop right after the punchline
T_BACK = [e for e in TL["events"] if e["type"] == "notify"][0]["pop"]   # theme returns with mom's notification
T_HAPPY = [k for k in TL["ko"] if k["state"] == "happy"][-1]["start"]   # Ko glows in the tail
T_LAST = TL["shots"][-1]["start"] + 0.3     # last chord lands
TAPE = 0.35


def load(path):
    x, sr = sf.read(str(path), always_2d=True, dtype="float64")
    if sr != SR:
        x = resample_poly(x, SR, sr, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2]


def fade(x, t0, t1, up=True):
    """Apply a cosine fade over [t0, t1] seconds (in place, stereo)."""
    a, b = int(t0 * SR), int(t1 * SR)
    r = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, b - a))
    x[a:b] *= (r if up else 1 - r)[:, None]
    if up:
        x[:a] = 0
    else:
        x[b:] = 0
    return x


def tape_stop(x, t0, dur=TAPE):
    """Speed drops 1 -> 0 over dur starting at t0; silence after. x: full-length stereo."""
    n = int(dur * SR)
    u = np.arange(n) / n
    speed = (1 - u) ** 1.6
    pos = t0 * SR + np.cumsum(speed)
    idx = np.arange(len(x))
    seg = np.stack([np.interp(pos, idx, x[:, c]) for c in range(2)], axis=1)
    seg *= ((1 - u) ** 0.8)[:, None]
    out = x.copy()
    a = int(t0 * SR)
    out[a:a + n] = seg
    out[a + n:] = 0
    return out


def speech_windows(pad_a=0.1, pad_b=0.15):
    return [(l["start"] - pad_a, l["end"] + pad_b) for l in TL["lines"]]


def gain_env(swell=True):
    """dB envelope per sample: -22 under lines, -12 in voiceless gaps >= 1.0 s, small swell at happy."""
    t = np.arange(N) / SR
    db = np.full(N, -22.0)
    w = speech_windows()
    gaps = [(0.0, w[0][0])] + [(w[i][1], w[i + 1][0]) for i in range(len(w) - 1)] + [(w[-1][1], DUR)]
    for a, b in gaps:
        if b - a >= 1.0:
            db[(t >= a + 0.2) & (t <= b - 0.2)] = -12.0
    if swell:
        m = (t >= T_HAPPY - 0.1) & (t < T_LAST)
        db[m] += 3.0 * np.clip((t[m] - (T_HAPPY - 0.1)) / 0.8, 0, 1)
    k = int(0.35 * SR)
    ker = np.hanning(k)
    ker /= ker.sum()
    pad = np.pad(db, (k, k), mode="edge")
    return np.convolve(pad, ker, mode="same")[k:-k]


def voice_rms_db():
    v = load(ROOT / "voice" / "voice.wav").mean(axis=1); sr = SR
    m = np.zeros(len(v), bool)
    for a, b in speech_windows(0, 0):
        m[int(a * sr):int(b * sr)] = True
    return 20 * np.log10(np.sqrt(np.mean(v[m] ** 2)))


def to_stem(raw):
    """raw: full-length stereo music (pre-level). Normalise active RMS to the voice RMS, apply envelope."""
    act = np.abs(raw).max(axis=1) > 1e-4
    rms = np.sqrt(np.mean(raw[act] ** 2))
    scale = 10 ** (voice_rms_db() / 20) / rms
    env = 10 ** (gain_env() / 20)
    return raw * scale * env[:, None]
