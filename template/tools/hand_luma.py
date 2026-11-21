# max luma in the hand box (+-60 px at 1080 w) of code/snapshots frames; limit <= 241 (not blown out).
# usage (from anywhere): python tools/hand_luma.py hands.json   ({"5.2": [[x,y],...], ...} normalised hand centres from tools/hand_boxes.mjs; keys = snapshot times)
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import sys, glob, os, json
from PIL import Image
import numpy as np
hs = json.load(open(sys.argv[1], encoding='utf-8'))
fs = {f.split('at-')[1][:-5].rstrip('s'): f for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'code', 'snapshots', 'frame-*.png'))}
worst = 0
for k, pts in hs.items():
    im = np.asarray(Image.open(fs[k]).convert('L')).astype(float); h, w = im.shape; r = 60 * w / 1080
    face = im[int(h*.28):int(h*.5), int(w*.4):int(w*.8)].max()
    for x, y in pts:
        cx, cy = int(x * w), int(y * h)
        m = im[max(0, int(cy-r)):int(cy+r), max(0, int(cx-r)):int(cx+r)]
        if m.size == 0: continue
        worst = max(worst, m.max()); print(k, (round(x, 2), round(y, 2)), 'hand max luma', m.max(), '| face-zone max', face)
print('worst hand luma', worst, 'OK' if worst <= 241 else 'OVER 241')
