"""Write code/passport.js from passports:  python characters/use.py guy.json [ko.json]
Paths: relative to this folder (or the cwd), or absolute. No arguments = the defaults (guy.json + ko.json).
code/index.html reads window.PASSPORTS and passes each passport to characters.js."""
for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))


def load(n):
    p = n if os.path.isabs(n) or os.path.exists(n) else os.path.join(here, n)
    return json.load(open(p, encoding='utf-8'))


a = sys.argv[1:] or ['guy.json', 'ko.json']
guy, ko = load(a[0]), load(a[1] if len(a) > 1 else 'ko.json')
out = os.path.join(here, '..', 'code', 'passport.js')
open(out, 'w', encoding='utf-8').write('// written by characters/use.py - edit the JSON passports, not this file\nwindow.PASSPORTS = ' + json.dumps({'guy': guy, 'ko': ko}, ensure_ascii=False) + ';\n')
print('passport.js <-', a)
