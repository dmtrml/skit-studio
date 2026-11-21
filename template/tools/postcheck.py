"""Post-render check of a skit draft.

    python tools/postcheck.py VIDEO SNAPDIR SHEET_OUT

SNAPDIR holds hyperframes snapshots of the same look at two times (frame-NN-at-<t>s.png, any t; render_draft.sh makes 0 and duration/2).
Prints: video/audio durations (want both = timeline duration), mean luma of the last 3 frames, mean abs diff (0..255, 480x854 gray)
of the render's frame vs the snapshot at each time (2-worker seek bug if > ~3: re-render with --workers 1), and writes a 1 fps contact sheet.
Exit code 3 when a diff > 3.
"""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import glob
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from paths import PB, SKIT

video, snapdir, sheet = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
TLJ = json.loads((SKIT / 'timeline.json').read_text(encoding='utf-8'))
FPS, N, DUR = TLJ['fps'], TLJ['frames'], TLJ['duration']


def probe():
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,duration', '-of', 'json', str(video)],
                       capture_output=True, text=True)
    return {s['codec_type']: float(s.get('duration', 0)) for s in json.loads(r.stdout)['streams']}


def frame_at(n):
    cmd = ['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f"select=eq(n\\,{n})", '-vsync', '0', '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']
    return Image.open(io.BytesIO(subprocess.run(cmd, capture_output=True).stdout))


def gray(im):
    return im.convert('L').resize((480, 854), Image.BILINEAR)


d = probe()
print(f"video {d.get('video', 0):.3f} s, audio {d.get('audio', 0):.3f} s (want {DUR:.3f} both)")
lum = [ImageStat.Stat(gray(frame_at(k))).mean[0] for k in (N - 3, N - 2, N - 1)]
print('last 3 frames luma:', ' '.join(f'{v:.1f}' for v in lum))
worst = 0
for p in sorted(glob.glob(str(snapdir / 'frame-*-at-*.png')))[:2]:
    t = float(os.path.basename(p).split('at-')[1][:-5].rstrip('s'))
    a, b = gray(frame_at(round(t * FPS))), gray(Image.open(p))  # by frame index: -ss lands a frame or two late
    v = ImageStat.Stat(ImageChops.difference(a, b)).mean[0]
    worst = max(worst, v)
    print(f't={t:g}: render vs snapshot mean abs diff {v:.2f}')
times = ','.join(f'{i + .5:.1f}' for i in range(int(DUR)))
subprocess.run([sys.executable, str(PB / 'frame_sheet.py'), str(video), times, str(sheet), '--cols', '8', '--width', '240'], check=True)
print('sheet', sheet)
if worst > 3:
    print('WARN: diff > 3 -> re-render with --workers 1')
    sys.exit(3)
