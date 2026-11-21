"""Contact sheet of snapshot PNGs: python tools/sheet_shots.py SNAPDIR OUT.jpg [cols=6]
Tiles 270x480, labelled with the time parsed from frame-NN-at-<t>s.png, sorted by time."""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import glob, os, sys
from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
tm = lambda f: float(os.path.basename(f).split('at-')[1][:-5].rstrip('s'))
fs = sorted(glob.glob(os.path.join(d, 'frame-*.png')), key=tm)
cols = max(1, min(cols, len(fs)))
rows = (len(fs) + cols - 1) // cols
S = Image.new('RGB', (cols * 270, rows * 480))
dr = ImageDraw.Draw(S)
for i, f in enumerate(fs):
    x, y = (i % cols) * 270, (i // cols) * 480
    S.paste(Image.open(f).convert('RGB').resize((270, 480), Image.LANCZOS), (x, y))
    dr.text((x + 4, y + 4), f'{tm(f):g}s', fill=(255, 255, 0))
S.save(out, quality=85)
print(out, len(fs), 'tiles')
