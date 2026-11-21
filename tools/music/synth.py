"""Skit 3 «Как сын»: numpy synth of a warm "home / mom" theme -> music_b_raw.wav (full length, pre-level). Seeded.
From skit 2 synth.py: key F, slower, lullaby melody; part 2 = one bar from the notification pop to the last chord."""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter

from common import *  # noqa

rng = np.random.default_rng(7)
BPM1, BPM2 = 72.0, 60.0 / ((T_LAST - T_BACK) / 1 / 4)   # part 2: 1 bar fills T_BACK -> last chord

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
def midi(s):  # "F#4"
    n = NOTE[s[0]] + (1 if "#" in s else 0)
    return 12 * (int(s[-1]) + 1) + n

CH = {  # name: (bass, comp voicing)
    "Fmaj7": ("F1", ["A3", "C4", "E4", "F4"]),
    "Dm7": ("D2", ["F3", "A3", "C4", "D4"]),
    "Bbmaj7": ("A#1", ["D4", "F4", "A4", "A#3"]),
    "C7sus4": ("C2", ["A#3", "F4", "G4", "C4"]),
}
# melody per bar: (beat, note, length in beats)
MEL = {
    "Fmaj7": [(0, "C5", 1), (1, "A4", 1), (2, "C5", 1), (3, "F5", 1)],
    "Dm7": [(0, "E5", 2), (2, "D5", 1), (3, "A4", 1)],
    "Bbmaj7": [(0, "D5", 1), (1, "F5", 1), (2, "A5", 1.5), (3.5, "G5", .5)],
    "C7sus4": [(0, "F5", 1.5), (1.5, "E5", .5), (2, "G5", 2)],
}
PROG = ["Fmaj7", "Dm7", "Bbmaj7", "C7sus4"]


def rhodes(freq, dur, vel, bright=1.0, sr=SR):
    """FM e-piano: carrier + 1:1 body mod + short tine (ratio 14) at the attack; decays; stereo detune."""
    n = int((dur + 1.2) * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    for ch, det in enumerate((0.9996, 1.0004)):
        f = freq * det
        idx = (1.2 + 1.8 * vel) * bright * np.exp(-t / 0.9)
        tine = 0.5 * vel * bright * np.exp(-t / 0.05)
        ph = 2 * np.pi * f * t
        y = np.sin(ph + idx * np.sin(ph) + tine * np.sin(14 * ph))
        y += 0.15 * np.sin(2 * ph) * np.exp(-t / 0.4)
        out[:, ch] = y
    env = np.minimum(t / 0.004, 1) * np.exp(-t / (1.6 + 0.3 * dur))
    rel = np.clip((dur + 0.5 - t) / 0.5, 0, 1)            # release after note length
    out *= (env * rel)[:, None] * vel * 0.25
    return out


def bell(freq, vel):
    n = int(2.0 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.3)
    y *= np.minimum(t / 0.002, 1) * np.exp(-t / 0.7) * vel * 0.12
    return np.stack([y, y], 1)


def bass(freq, dur, vel):
    n = int((dur + 0.3) * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t) * np.exp(-t / .2)
    y *= np.minimum(t / 0.01, 1) * np.clip((dur + 0.2 - t) / 0.2, 0, 1) * vel * 0.32
    return np.stack([y, y], 1)


def brush(kind, vel):
    n = int(0.22 * SR) if kind == "snare" else int(0.06 * SR)
    t = np.arange(n) / SR
    z = rng.standard_normal(n)
    lo, hi = (1500, 7000) if kind == "snare" else (6000, 12000)
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
    y = lfilter(b, a, z) * np.exp(-t / (0.07 if kind == "snare" else 0.015))
    y *= np.minimum(t / 0.01, 1) * vel * (0.06 if kind == "snare" else 0.025)
    return np.stack([y, y * 0.9], 1)


def put(buf, snd, t):
    a = int(round(t * SR))
    if a < 0 or a >= len(buf):
        return
    b = min(len(buf), a + len(snd))
    buf[a:b] += snd[:b - a]


def human(t):
    return t + rng.normal(0, 0.007)


def bar_events(buf, chord, t0, spb, melody_up, lead_bell, dense, final=False):
    bassn, voicing = CH[chord]
    # bass
    put(buf, bass(mtof(midi(bassn)), spb * (4 if final else 1.8), 0.9), t0)
    if not final:
        put(buf, bass(mtof(midi(bassn)), spb * 1.4, 0.6), human(t0 + 2.5 * spb))
    # comp: strummed chord on 1, softer re-hit on the "and" of 2
    hits = [(0, 0.55, 3.8)] if final else [(0, 0.55, 2.2), (1.5, 0.35, 1.2)] + ([(3, 0.28, 0.9)] if dense else [])
    for beat, v, ln in hits:
        for k, nn in enumerate(voicing):
            vel = float(np.clip(v + rng.normal(0, 0.05), 0.1, 1))
            put(buf, rhodes(mtof(midi(nn) + (12 if melody_up and final else 0)), ln * spb, vel), human(t0 + beat * spb + k * 0.014))
    # melody
    mel = MEL[chord] if not final else [(0, "C5", 4), (0, "F5", 4)]
    for beat, nn, ln in mel:
        vel = float(np.clip(0.7 + rng.normal(0, 0.06), 0.3, 1))
        m = midi(nn) + (12 if melody_up else 0)
        put(buf, rhodes(mtof(m), ln * spb, vel, bright=1.15 if melody_up else 1.0), human(t0 + beat * spb))
        if lead_bell:
            put(buf, bell(mtof(m + 12), vel), human(t0 + beat * spb))
    # drums
    for b in (1, 3):
        put(buf, brush("snare", 0.9 + rng.normal(0, .05)), human(t0 + b * spb))
    if not final:
        for b in np.arange(0, 4, 0.5):
            put(buf, brush("hat", (0.8 if b % 1 == 0 else 0.5) + rng.normal(0, .08)), human(t0 + b * spb))


def reverb(x, wet=0.28):
    n = int(1.9 * SR); t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n) * np.exp(-t / 0.55) for _ in range(2)], 1)
    b, a = butter(1, 5000 / (SR / 2))
    ir = lfilter(b, a, ir, axis=0)
    ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(0))
    w = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - wet * .5) + w * wet * 1.2


def main():
    buf = np.zeros((N + SR * 3, 2))
    spb1 = 60 / BPM1
    t = T_START
    bar = 0
    while t < T_STOP + 0.2:
        bar_events(buf, PROG[bar % 4], t, spb1, melody_up=False, lead_bell=False, dense=bar >= 4)
        t += 4 * spb1; bar += 1
    p1 = buf[:N].copy()
    buf2 = np.zeros_like(buf)
    spb2 = 60 / BPM2
    t = T_BACK
    for i, ch in enumerate(["Bbmaj7"]):
        bar_events(buf2, ch, t, spb2, melody_up=True, lead_bell=True, dense=True)
        t += 4 * spb2
    bar_events(buf2, "Fmaj7", T_LAST, spb2, melody_up=True, lead_bell=True, dense=False, final=True)
    p2 = buf2[:N].copy()
    p1 = fade(reverb(p1), T_START, T_START + 0.6, up=True)
    p1 = tape_stop(p1, T_STOP)
    p2 = reverb(p2, 0.34)
    p2 = fade(p2, T_BACK - 0.01, T_BACK + 0.12, up=True)
    p2 = fade(p2, DUR - 0.8, DUR, up=False)
    # vinyl crackle, part 1 only, very faint
    crack = np.zeros(N)
    for tt in np.sort(rng.uniform(T_START, T_STOP, 160)):
        crack[int(tt * SR)] = rng.normal(0, 0.012)
    cr = lfilter(*butter(1, 2500 / (SR / 2), "high"), crack)
    p1[:, 0] += cr; p1[:, 1] += np.roll(cr, 37)
    p1 = tape_stop(p1, T_STOP) if False else p1
    raw = p1 + p2
    sf.write(str(HERE / "music_b_raw.wav"), raw, SR, subtype="FLOAT")
    print("BPM2 %.2f bar2 %.3f s; peak %.3f" % (BPM2, 240 / BPM2, np.abs(raw).max()))


if __name__ == "__main__":
    main()
