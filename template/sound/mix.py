"""Build the sound bed (everything except the voice) and a preview mix.

Room tone + guy typing (cues typing/enter) + generic one-shots (cues sfx: {t, src: file in sound/src | preset ding|tick|pop|limit, db, dur?}).
Music is NOT here.
Reads ../cues.json, writes sfx_bed.wav (duration from ../timeline.json, 48 kHz, stereo) and
preview_mix.wav = bed + ../voice/voice.wav (voice untouched in gain).
Sources are in ./src (see LICENSES.md; downloaded by install.py, not shipped). Needs numpy + soundfile; ffmpeg is
used to decode the mp3 sources and to measure loudness.
"""
import json
import sys
import os
import re
import subprocess

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src")
SR = 48000
DUR = json.load(open(os.path.join(ROOT, 'timeline.json'), encoding='utf-8'))['duration']
N = int(round(DUR * SR))
RNG = np.random.default_rng(20260809)

rows = []  # (cue, time, peak_dbfs)


def decode(path):
    if not os.path.isfile(path):
        sys.exit(f"нет звука {os.path.basename(path)} в sound/src/: python <plugin>/scripts/install.py --install --only sfx, "
                 "потом скопируйте ~/.skit-studio/sfx/*.mp3 в sound/src/ (звуки Mixkit не входят в плагин по лицензии)")
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64).reshape(-1, 2)


def peak(x):
    return float(np.max(np.abs(x))) if x.size else 0.0


def db(x):
    return 20 * np.log10(max(x, 1e-12))


def norm_peak(x, dbfs):
    p = peak(x)
    return x * (10 ** (dbfs / 20) / p) if p > 0 else x


def place(bed, clip, t):
    i = int(round(t * SR))
    n = min(len(clip), N - i)
    if n <= 0:
        return
    bed[i:i + n] += clip[:n]


def fade_out(x, sec):
    k = min(int(sec * SR), len(x))
    x[len(x) - k:] *= np.linspace(1, 0, k)[:, None] if x.ndim == 2 else np.linspace(1, 0, k)
    return x


def shaped_noise(n, exponent, rng):
    """White noise shaped to amplitude ~ f^-exponent (1 = brown, 0.5 = pink)."""
    W = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    return np.fft.irfft(W * f ** (-exponent), n)


def lowpass_shape(f, fc):
    return 1 / np.sqrt(1 + (f / fc) ** 4)


def highpass_shape(f, fc):
    return 1 / np.sqrt(1 + (fc / f) ** 4)


def band_noise(n, exponent, lo, hi, rng):
    W = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    amp = f ** (-exponent) * highpass_shape(f, lo) * lowpass_shape(f, hi)
    return np.fft.irfft(W * amp, n)


def biquad_lowpass(x, fc, q=0.707):
    w0 = 2 * np.pi * fc / SR
    alpha = np.sin(w0) / (2 * q)
    cw = np.cos(w0)
    a0 = 1 + alpha
    b0, b1, b2 = (1 - cw) / 2 / a0, (1 - cw) / a0, (1 - cw) / 2 / a0
    a1, a2 = -2 * cw / a0, (1 - alpha) / a0
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(x):
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        y[i] = yi
        x2, x1, y2, y1 = x1, xi, y1, yi
    return y


def tri(f, t):
    return 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))


def tone_seg(f, dur, att=0.005, rel=0.005):
    t = np.arange(int(round(dur * SR))) / SR
    e = np.ones_like(t)
    a, r = int(att * SR), int(rel * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return tri(f, t) * e


def rate_change(x, r):
    idx = np.arange(int(len(x) / r)) * r
    src = np.arange(len(x))
    return np.stack([np.interp(idx, src, x[:, c]) for c in range(x.shape[1])], axis=1)


def _st(x):
    return np.stack([x, x], axis=1)


def preset_ding():      # two-tone bell
    n_d = int(0.9 * SR)
    td = np.arange(n_d) / SR
    ding = np.zeros(n_d)
    for f0, amp in ((1320, 1.0), (1760, 0.85)):
        for k, (mult, a) in enumerate(((1, 1.0), (2.76, 0.35), (5.4, 0.12))):
            ding += amp * a * np.sin(2 * np.pi * f0 * mult * td) * np.exp(-td / (0.6 / (1 + 0.8 * k)) * 1.0)
    att = int(0.005 * SR)
    ding[:att] *= np.linspace(0, 1, att)
    return _st(fade_out(ding, 0.05))


def preset_tick():      # marker tick, 2.4 kHz
    tm = np.arange(int(0.06 * SR)) / SR
    tick = np.sin(2 * np.pi * 2400 * tm) * np.exp(-tm / 0.012)
    tick[:int(0.001 * SR)] *= np.linspace(0, 1, int(0.001 * SR))
    return _st(tick)


def preset_pop():       # soft bubble pop: short falling sine
    tp = np.arange(int(0.12 * SR)) / SR
    pop = np.sin(2 * np.pi * (900 - 4000 * tp) * tp) * np.exp(-tp / 0.03)
    pop[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return _st(pop)


def preset_limit():     # "denied": two triangle tones 523/392 Hz + glitch from src
    t_tone = biquad_lowpass(np.concatenate([tone_seg(523, 0.11), tone_seg(392, 0.16)]), 3000)
    tone_st = _st(t_tone)
    glitch = fade_out(decode(os.path.join(SRC, "glitch-virtual-quick.mp3"))[:int(0.35 * SR)].copy(), 0.08)
    lim = np.zeros((max(len(tone_st), len(glitch)), 2))
    lim[:len(tone_st)] += norm_peak(tone_st, 1.0)
    lim[:len(glitch)] += 0.7 * norm_peak(glitch, 1.0)
    return lim


PRESETS = {"ding": preset_ding, "tick": preset_tick, "pop": preset_pop, "limit": preset_limit}


def main():
    cues = json.load(open(os.path.join(ROOT, "cues.json"), encoding="utf-8"))
    bed = np.zeros((N, 2))

    # 1. room tone, whole length
    n = N
    brown = shaped_noise_lp = None
    brown_l = []
    fan_l = []
    for c in range(2):
        b = shaped_noise(n, 1.0, RNG)
        b = np.fft.irfft(np.fft.rfft(b) * lowpass_shape(np.fft.rfftfreq(n, 1 / SR), 300), n)
        fn = band_noise(n, 0.5, 300, 1500, RNG)
        brown_l.append(b / np.sqrt(np.mean(b ** 2)))
        fan_l.append(fn / np.sqrt(np.mean(fn ** 2)))
    room = np.stack(brown_l, axis=1) + 0.25 * np.stack(fan_l, axis=1)
    room *= (10 ** (-50 / 20)) / np.sqrt(np.mean(room ** 2))
    fi = int(0.3 * SR)
    room[:fi] *= np.linspace(0, 1, fi)[:, None]
    bed += room
    rows.append(("room tone (RMS -50 dBFS, fade-in 0.3 s)", 0.0, db(peak(room))))

    # 2. keys
    click_full = decode(os.path.join(SRC, "sfx-keyboard-click.mp3"))
    click = click_full[:int(0.15 * SR)]
    for kt in cues.get("typing", []):
        soft = bool(kt.get("soft", False))
        for t in kt["keys"]:
            r = 1 + RNG.uniform(-0.04, 0.04)
            g = RNG.uniform(-2, 2)
            x = rate_change(click, r)
            x = fade_out(x, 0.02)
            x = norm_peak(x, (-31 if soft else -26) + g)
            place(bed, x, t)
            rows.append(("key" + (" (soft)" if soft else ""), t, db(peak(x))))

    # 3. enter
    ent = norm_peak(decode(os.path.join(SRC, "typewriter-hit-soft.mp3")), -22)
    for t in cues.get("enter", []):
        place(bed, ent, t)
        rows.append(("enter", t, db(peak(ent))))

    # 4. generic one-shots: cues["sfx"] = [{t, src: file in sound/src | preset name, db: peak dBFS, dur?: keep seconds}]
    for sx in cues.get("sfx", []):
        name = sx["src"]
        if name in PRESETS:
            clip = PRESETS[name]()
        else:
            clip = decode(os.path.join(SRC, name))
        if sx.get("dur"):
            clip = clip[:int(sx["dur"] * SR)].copy()
            clip = fade_out(clip, min(0.08, sx["dur"] / 2))
        clip = norm_peak(clip, sx.get("db", -24))
        place(bed, clip, sx["t"])
        rows.append((f"sfx {name}", sx["t"], db(peak(clip))))

    sf.write(os.path.join(HERE, "sfx_bed.wav"), bed, SR, subtype="PCM_24")
    import shutil
    shutil.copyfile(os.path.join(HERE, "sfx_bed.wav"), os.path.join(ROOT, "code", "assets", "sfx_bed.wav"))

    voice = decode(os.path.join(ROOT, "voice", "voice.wav"))
    voice = np.vstack([voice, np.zeros((max(0, N - len(voice)), 2))])[:N]
    prev = bed + voice
    sf.write(os.path.join(HERE, "preview_mix.wav"), prev, SR, subtype="PCM_24")

    print(f"{'cue':<42}{'time_s':>9}{'peak_dBFS':>11}")
    for name, t, pk in rows:
        print(f"{name:<42}{t:>9.3f}{pk:>11.1f}")
    print(f"bed length: {len(bed)} samples = {len(bed) / SR:.3f} s; bed peak {db(peak(bed)):.1f} dBFS")
    print(f"preview peak {db(peak(prev)):.1f} dBFS (voice untouched)")

    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i",
                        os.path.join(HERE, "preview_mix.wav"),
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    seg = txt[txt.rfind("Integrated loudness"):]
    mi = re.search(r"I:\s+(-?[\d.]+) LUFS", seg)
    mr = re.search(r"LRA:\s+([\d.]+) LU", seg)
    tp = txt[txt.rfind("True peak"):]
    mp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tp)
    print(f"preview integrated loudness: {mi.group(1) if mi else '?'} LUFS; "
          f"LRA {mr.group(1) if mr else '?'} LU; true peak {mp.group(1) if mp else '?'} dBFS")


if __name__ == "__main__":
    main()
