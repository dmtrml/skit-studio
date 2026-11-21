"""cues.src.json + timeline.json -> cues.json (absolute seconds) + code/cues.js.

    python tools/cues.py

Any string value matching ^(L|S)(\\d+)\\.(s|e)([+-]\\d+(\\.\\d+)?)?$ becomes that line's / shot's start (s) or end (e) plus the offset:
  "L3.s+0.2" = 0.2 s after line 3 starts, "S5.e-0.1" = 0.1 s before shot 5 ends.
Event refs: "<event type>.<key>[+-offset]" reads a number from timeline.json events, e.g. "chat1.reply+0.1", "chat2.mark".
A gesture may give t + end instead of dur. Run order: prep.py, cues.py, sound/mix.py.
Also syncs data-duration in code/index.html with timeline.json.
"""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import json
import re

from paths import SKIT as ROOT

PAT = re.compile(r"^(L|S)(\d+)\.(s|e)([+-]\d+(\.\d+)?)?$")
EPAT = re.compile(r"^([A-Za-z]\w*)\.([A-Za-z]\w*)([+-]\d+(\.\d+)?)?$")
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
byid = {x["id"]: x for x in tl["lines"] + tl["shots"]}
ev = {e["type"]: e for e in tl["events"]}


def res(v):
    if isinstance(v, str):
        m = PAT.match(v)
        if m:
            o = byid[f"{m.group(1)}{m.group(2)}"]
            return round(o["start" if m.group(3) == "s" else "end"] + float(m.group(4) or 0), 3)
        m = EPAT.match(v)
        if m and m.group(1) in ev and isinstance(ev[m.group(1)].get(m.group(2)), (int, float)):
            return round(ev[m.group(1)][m.group(2)] + float(m.group(3) or 0), 3)
        return v
    if isinstance(v, list):
        return [res(x) for x in v]
    if isinstance(v, dict):
        d = {k: res(x) for k, x in v.items()}
        if "end" in d and "t" in d and "dur" not in d:   # gesture: t + end -> dur
            d["dur"] = round(d.pop("end") - d["t"], 3)
        return d
    return v


src = json.loads((ROOT / "cues.src.json").read_text(encoding="utf-8"))
out = res(src)
(ROOT / "cues.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "code" / "cues.js").write_text("window.CUES=" + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
ix = ROOT / "code" / "index.html"
if ix.exists():
    ix.write_text(re.sub(r'data-duration="[\d.]+"', f'data-duration="{tl["duration"]}"', ix.read_text(encoding="utf-8")), encoding="utf-8")
print("cues.json + code/cues.js:", ", ".join(k for k in out if k != "note"))
