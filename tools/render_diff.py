"""Where do two renders of the same block differ? Prints time ranges, ≤ ~20 lines.

    python <plugin>/tools/render_diff.py OLD.mp4 NEW.mp4 [--fps 10] [--size 960x540]
        [--offset 0] [--expect 5.8-7.4,16-19.6] [--cell-thr 6] [--ignore "0,930,1920,1080@31.5-126.6;..."]

Both videos are decoded in gray at --size and streamed frame by frame (no big memory).
The frame is split into 16x9 cells (120x120 px of the 1920x1080 frame at any --size); a frame
differs when one cell's mean absolute difference (0-255) is above --cell-thr. Half size keeps
small text sharp, so a privacy blur that went missing shows up.
--offset shifts NEW against OLD (NEW t = OLD t + offset), e.g. when a block got a longer head.
--expect lists planned ranges (NEW time); everything else is printed as NEW and fails the run.
--ignore masks planned changes in one area only (x0,y0,x1,y1 in 1920x1080 px, @t0-t1 in NEW time),
so the rest of the frame is still compared — e.g. a small Ko riding a progress strip for 90 s.
"""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import argparse
import subprocess
import sys

import numpy as np

GX, GY = 16, 9


def reader(path, fps, w, h, start=0.0):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-vf", f"fps={fps},scale={w}:{h}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = w * h
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w).astype(np.int16)
    proc.stdout.close()
    proc.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--fps", type=float, default=10)
    ap.add_argument("--size", default="960x540")
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--expect", default="")
    ap.add_argument("--cell-thr", type=float, default=6.0)
    ap.add_argument("--ignore", default="")
    a = ap.parse_args()
    w, h = (int(x) for x in a.size.split("x"))
    cw, ch = w // GX, h // GY
    shift = max(0.0, a.offset)
    expect = [tuple(float(x) for x in r.split("-")) for r in a.expect.split(",") if r]
    k = w / 1920
    ignore = []
    for item in filter(None, a.ignore.split(";")):
        box, span = item.split("@")
        x0, y0, x1, y1 = (round(float(v) * k) for v in box.split(","))
        t0, t1 = (float(v) for v in span.split("-"))
        ignore.append((x0, y0, x1, y1, t0, t1))

    rows = []  # (new time, worst cell value, cell index)
    for i, (f0, f1) in enumerate(zip(reader(a.old, a.fps, w, h), reader(a.new, a.fps, w, h, shift))):
        d = np.abs(f0 - f1)
        t = i / a.fps + shift
        for x0, y0, x1, y1, t0, t1 in ignore:
            if t0 <= t <= t1:
                d[y0:y1, x0:x1] = 0
        d = d[: ch * GY, : cw * GX].reshape(GY, ch, GX, cw).mean(axis=(1, 3)).ravel()
        rows.append((t, float(d[j := int(d.argmax())]), j))

    spans, cur = [], None
    for t, v, k in rows:
        if v > a.cell_thr:
            if cur and t - cur[1] <= 1.5 / a.fps:
                cur[1] = t
                if v > cur[2]:
                    cur[2], cur[3] = v, k
            else:
                cur = [t, t, v, k]
                spans.append(cur)
    print(f"{len(rows) / a.fps:.1f} s compared @ {a.fps:g} fps {w}x{h}, cell thr {a.cell_thr}: {len(spans)} range(s)")
    bad = 0
    for t0, t1, v, k in spans:
        planned = any(t0 >= e0 - .3 and t1 <= e1 + .3 for e0, e1 in expect)
        bad += not planned
        x, y = k % GX * 120, k // GX * 120
        print(f"  {'ok ' if planned else 'NEW'} {t0:7.2f}-{t1 + 1 / a.fps:7.2f}  worst {v:5.1f} @ x{x}-{x + 120} y{y}-{y + 120}")
    print(f"unexpected: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
