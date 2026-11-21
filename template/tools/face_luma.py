# max luma and count of clipped (>=250) pixels in the face+neck box of B-shot snapshots (code/snapshots). limit: max <= 230, 0 clipped.
# usage (from anywhere): python tools/face_luma.py 8.5 22.5 24.5
# ONLY times inside cam B shots: the box is where the guy's face is in shot B. In shot A it lands on Ko's top corner
# (its specular highlight reads 245-246 by design), so an A-shot number means nothing.
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import sys, glob, os
from PIL import Image
import numpy as np
fs = {f.split('at-')[1][:-5].rstrip('s'): f for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'code', 'snapshots', 'frame-*.png'))}
for k in sys.argv[1:]:
    im = np.asarray(Image.open(fs[k]).convert('L')).astype(float); h, w = im.shape
    b = im[int(h*.30):int(h*.62), int(w*.45):int(w*.80)]
    print(f't={k}: face+neck box max luma {b.max():.0f}, pixels >=250: {(b >= 250).sum()}, >=235: {(b >= 235).sum()}')
