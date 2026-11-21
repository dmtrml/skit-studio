"""Voice take -> final voice track with comic pauses + timeline.json + voice/envelope.json + code/data.js (+ code/assets/voice.wav).

    python tools/prep.py            (from anywhere; works on the skit folder that contains tools/)

Input: voice/take1.wav (one TTS take, all lines) + voice/take1.words.json (Whisper, word level).
Output: voice/voice.wav, timeline.json, voice/envelope.json, code/data.js, code/assets/voice.wav, data-duration in code/index.html.

Line texts come from the approved script (LINES); Whisper only gives word COUNTS -> rough line spans, then each
boundary is cut in the longest silence (< -50 dB) near it (Whisper word times run ~0.2 s early), so no line is clipped.

THE TABLES (edit these four, everything else is generic). Worked example = skit 2 «Плюс один» (kept in the comments).

LINES  rows (speaker, caption text, Whisper word count, pause BEFORE the line on the final timeline in s | None = keep the take's gap)
         speaker is "guy" or "ko" (anything else is treated as ko). A take line can be split into several caption lines
         (give each part its word count) to put a comic beat inside it.
         The word counts must sum to the number of Whisper words (assert).
SHOTS  function (s, e, D) -> rows (id, cam, start_s, extra)
         cam: "A" wide, "B" guy close, "C" Ko close, "INSERT" (a full-screen insert, extra {"ins": "<name>"} names the
         insert in code/inserts/). extra may also hold "push" (dolly amount 0..1) and "ease" (power on the dolly progress).
         s(i), e(i) = start/end of line i (1-based, as in LINES); D = total duration. The last shot ends at the duration.
KO     function (s, e, D) -> rows {"state", "start", "end"}   states: squint, think, blink, happy, red, stars (normal = none)
EVENTS function (s, e, D) -> rows {"type", "start", ...extra times}   data for the inserts / props (e.g. chat1: sent, reply),
         read by code/inserts/<type>.js and referenced from cues.src.json as E-refs, e.g. "chat1.reply+0.1".

MIN_GAP  smallest pause when a row says None. TAIL  final wide shot after the last line.
"""
from __future__ import annotations

for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import json
import math
import re
import shutil
import wave

import numpy as np

from paths import SKIT as ROOT

FPS = 30

# --- table 1: lines. ACTIVE = 3-line demo. Skit 2 had 18 rows, e.g.:
#   ("guy", "Ко, она ответила! Что писать?", 5, 0.6), ("ko", "Опять я?", 2, 0.45), ...,
#   ("ko", "Она ответила за две секунды.", 5, 3.15),   # long pause = room for a chat insert
#   ("ko", "Прийти.", 1, 0.4), ("ko", "Ты — плюс один.", 3, 0.45)
LINES = [
    ("guy", "Ко, она ответила! Что писать?", 5, 0.6),
    ("ko", "Опять я?", 2, 0.45),
    ("guy", "Ты написал первые три сообщения. Нельзя же вдруг поменять стиль.", 10, 0.3),
]
MIN_GAP = 0.12
TAIL = 2.0          # final wide shot after the last line (skit 2: Ko glows, the guy lowers the phone)


# --- table 2: shots. ACTIVE = A / C / B demo. Skit 2:
#   i1 = e(4) + 0.25   # chat insert 1 start
#   ("S1","A",0.0,{}), ("S2","C",s(2)-0.1,{}), ("S3","B",s(3)-0.1,{}), ("S4","C",e(3)+0.15,{}),
#   ("S5","INSERT",i1,{"ins":"chat1"}), ("S6","C",i1+2.7,{}), ..., ("S9","B",e(8)+0.25,{"push":0.08,"ease":1.7}), ...
def SHOTS(s, e, D):
    return [
        ("S1", "A", 0.0, {}),
        ("S2", "C", s(2) - 0.1, {}),
        ("S3", "B", s(3) - 0.1, {}),
    ]


# --- table 3: Ko states. Skit 2:
#   {"state":"squint","start":s(2),"end":e(2)+0.3}, {"state":"think","start":e(3)+0.15,"end":s(4)},
#   {"state":"blink","start":s(13)-0.1,"end":s(13)+0.25}, {"state":"happy","start":s(17)-0.3,"end":D+1}
def KO(s, e, D):
    return [
        {"state": "squint", "start": s(2), "end": e(2) + 0.3},
    ]


# --- table 4: events for inserts/props. Skit 2:
#   {"type":"chat1","start":i1,"sent":i1+0.35,"reply":i1+0.95}, {"type":"chat2","start":e(7)+0.15,"mark":s(8)+0.35}
def EVENTS(s, e, D):
    return []


def main() -> None:
    with wave.open(str(ROOT / "voice/take1.wav")) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // 100
    db = 20 * np.log10(np.sqrt((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1)) + 1e-9)

    d = json.loads((ROOT / "voice/take1.words.json").read_text(encoding="utf-8"))
    words = [w for s in d["segments"] for w in s["words"]]
    assert sum(n for _, _, n, _ in LINES) == len(words), (sum(n for _, _, n, _ in LINES), len(words))
    spans, i = [], 0
    for _, _, n, _ in LINES:
        spans.append((words[i]["start"], words[i + n - 1]["end"]))
        i += n

    # cut each line boundary in the longest silence (< -50 dB) near it
    loud = np.where(db > -45)[0]
    bounds = []   # (gap start, gap end) between line k and k+1
    for k in range(len(spans) - 1):
        a = int((spans[k][1] - 0.2) * 100)
        b = int((spans[k + 1][0] + 0.6) * 100)
        quiet = db[a:b] < -50
        best, run = None, None
        for j, q in enumerate(list(quiet) + [False]):
            if q and run is None:
                run = j
            elif not q and run is not None:
                if best is None or j - run > best[1] - best[0]:
                    best = (run, j)
                run = None
        if best is None or best[1] - best[0] < 4:      # no real gap (interruption): cut at the quietest frame
            m = int(np.argmin(db[a:b]))
            best = (m, m + 1)
        bounds.append(((a + best[0]) / 100, (a + best[1]) / 100))
    take = []
    for k in range(len(spans)):
        s = bounds[k - 1][1] - 0.03 if k else loud[0] / 100 - 0.03
        e = bounds[k][0] + 0.05 if k + 1 < len(spans) else (loud[-1] + 1) / 100 + 0.06
        if k:
            s = max(s, (bounds[k - 1][0] + bounds[k - 1][1]) / 2)
        if k + 1 < len(spans):
            e = min(e, (bounds[k][0] + bounds[k][1]) / 2)
        take.append((max(0.0, s), e))

    # place segments on the final timeline
    out, t, lines = [], 0.0, []
    fade = int(0.008 * sr)
    for k, ((spk, text, _, gap), (s, e)) in enumerate(zip(LINES, take)):
        if gap is None:
            gap = max(MIN_GAP, s - take[k - 1][1]) if k else 0.5
        t += gap
        seg = x[int(s * sr): int(e * sr)].copy()
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        out.append((t, seg))
        lines.append({"id": f"L{k + 1}", "speaker": spk, "text": text, "start": round(t, 3), "end": round(t + len(seg) / sr, 3)})
        t += len(seg) / sr
    L = lines
    end_voice = t
    duration = math.ceil((end_voice + 0.3 + TAIL) * 10) / 10       # x.y s -> frames = 3 * integer

    track = np.zeros(int(duration * sr), dtype=np.float32)
    for st, seg in out:
        i0 = int(st * sr)
        track[i0: i0 + len(seg)] += seg
    vdir = ROOT / "voice"
    with wave.open(str(vdir / "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())

    n = sr // FPS
    rms = np.sqrt((track[: len(track) // n * n].reshape(-1, n) ** 2).mean(axis=1))
    rms = np.clip(rms / (np.percentile(rms[rms > 1e-3], 95) + 1e-9), 0, 1)
    (vdir / "envelope.json").write_text(json.dumps({"fps": FPS, "rms": [round(float(v), 3) for v in rms]}), encoding="utf-8")

    def s(i): return L[i - 1]["start"]   # 1-based line numbers, as in LINES
    def e(i): return L[i - 1]["end"]
    shot_starts = SHOTS(s, e, duration)
    shots = []
    for k, (sid, cam, st, extra) in enumerate(shot_starts):
        en = shot_starts[k + 1][2] if k + 1 < len(shot_starts) else duration
        shots.append({"id": sid, "cam": cam, "start": round(st, 3), "end": round(en, 3), **extra})

    def rnd(row): return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}
    ko = [rnd(r) for r in KO(s, e, duration)]
    events = [rnd(r) for r in EVENTS(s, e, duration)]
    tl = {"duration": duration, "fps": FPS, "frames": round(duration * FPS), "shots": shots, "lines": lines, "ko": ko, "events": events}
    (ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    code = ROOT / "code"
    (code / "data.js").write_text("window.SKIT=" + json.dumps(tl, ensure_ascii=False) + ";\nwindow.RMS=" + json.dumps(json.loads((vdir / "envelope.json").read_text())["rms"]) + ";\n", encoding="utf-8")
    shutil.copyfile(vdir / "voice.wav", code / "assets/voice.wav")
    ix = code / "index.html"
    if ix.exists():       # data-duration of root, clip and audio tags
        ix.write_text(re.sub(r'data-duration="[\d.]+"', f'data-duration="{duration}"', ix.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"voice.wav {duration:.1f} s ({round(duration * FPS)} frames), voice ends {end_voice:.2f}")
    for sh in shots:
        print(f"{sh['id']:>4} {sh['cam']:<6} {sh['start']:6.2f}-{sh['end']:6.2f}")
    for ln in lines:
        print(f"{ln['id']:>4} {ln['speaker']:<3} {ln['start']:6.2f}-{ln['end']:6.2f} {ln['text']}")


if __name__ == "__main__":
    main()
