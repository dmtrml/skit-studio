"""One labelled contact sheet from a video: frames at given times in a grid, one JPG.

    python <plugin>/tools/frame_sheet.py VIDEO 10.3,10.9,11.1 OUT.jpg [--cols 4] [--width 480]
"""

from __future__ import annotations

for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def grab(video: Path, t: float, width: int) -> Image.Image:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={width}:-2,format=rgb24", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("times")
    ap.add_argument("out", type=Path)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=480)
    a = ap.parse_args()
    times = [float(x) for x in a.times.split(",") if x]
    tiles = [grab(a.video, t, a.width) for t in times]
    w, h = tiles[0].size
    rows = (len(tiles) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (w * a.cols, h * rows), (0, 0, 0))
    for i, (t, img) in enumerate(zip(times, tiles)):
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 86, 22), fill=(0, 0, 0))
        d.text((5, 5), f"{t:.2f}s", fill=(255, 255, 0))
        sheet.paste(img, ((i % a.cols) * w, (i // a.cols) * h))
    sheet.save(a.out, quality=82)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
