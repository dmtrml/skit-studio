"""Render a HyperFrames project with 4K supersampling: render at 3840x2160, average 2x2 down to 1920x1080.

    python tools/render_ss.py PROJECT_DIR OUT.mp4 [--fps 30] [--crf 18] [--keep-4k] [--hf VERSION] [--portrait]
--portrait: vertical pieces, 2160x3840 averaged down to 1080x1920 (ko-skit, 09.11).

Small, tilted screen recordings drawn at 1080p break into pixel stairs and shimmer from frame to frame. A 4K render
(Chrome at DPR 2, composition unchanged) box-averaged to 1080p antialiases text, thin frames and dot grids.
Block 3 v6 tunnel scene: shimmer -20...-38 %, render 2 min 7 s for 61 s (about the cost of a 1080p render).
Frames stream into the encoder (HF_CAPTURE_PARALLEL_STREAM=true): the disk path needs PNG space the drive may not have.
Audio is copied. Every block of a film goes through this script, so the encodes match and the blocks concat with -c copy.
"""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]

HF_FILE = Path(__file__).resolve().parent / "hf_version.txt"
HF_DEFAULT = HF_FILE.read_text(encoding="utf-8").strip() if HF_FILE.exists() else "latest"


def frames(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return int(out or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--keep-4k", action="store_true")
    ap.add_argument("--hf", default=HF_DEFAULT, help="HyperFrames CLI version (default: tools/hf_version.txt)")
    ap.add_argument("--portrait", action="store_true", help="vertical: portrait-4k -> 1080x1920")
    ap.add_argument("--workers", type=int, help="HyperFrames render workers (2 on a weak PC); default = auto")
    a = ap.parse_args()

    project, out = Path(a.project).resolve(), Path(a.out).resolve()
    k4, log = out.with_name(out.stem + "-4k.mp4"), out.with_name(out.stem + "-4k.log")
    cmd = ["npx", "--yes", f"hyperframes@{a.hf}", "render", "--resolution", "portrait-4k" if a.portrait else "landscape-4k", "-o", str(k4)]
    cmd += ["--fps", str(a.fps)] if a.fps else []
    cmd += ["--workers", str(a.workers)] if a.workers else []
    with open(log, "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, cwd=project, stdout=f, stderr=subprocess.STDOUT, shell=True,
                           env={**os.environ, "HF_CAPTURE_PARALLEL_STREAM": "true"})
    text = log.read_text(encoding="utf-8", errors="replace")
    done = re.search(r"rendered in [^\n]*", text)
    if r.returncode or not done or not k4.exists():
        fail = re.findall(r"(?:Render failed|Error:)[^\n]*", text)
        sys.exit(f"4K render failed ({r.returncode}): {fail[-1] if fail else 'see ' + str(log)}")
    print("4K:", done.group(0))

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(k4), "-map", "0:v", "-map", "0:a?",
                    "-vf", "scale=1080:1920:flags=area" if a.portrait else "scale=1920:1080:flags=area", "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow",
                    "-pix_fmt", "yuv420p", *COLOR, "-c:a", "copy", "-movflags", "+faststart", str(out)], check=True)
    n4, n = frames(k4), frames(out)
    print(f"1080p: {out.name}, {n} frames (4K {n4})")
    if n != n4:
        sys.exit("frame count mismatch")
    if not a.keep_4k:
        k4.unlink()


if __name__ == "__main__":
    main()
