# popcorn (prop)

Striped popcorn bucket slides to Ko; Ko squashes, hops, turns toward it, lands and leans back. Ported from skit 1 (`research/styles/ko-skit/code-v3`) onto the plug-in contract (`../README.md`): hooks `build`, `update` (bucket position) and `koFx` (Ko's squash / hop / turn / lean; the base applies `{sx, sy, by, rotY, rotX}` after every other Ko effect). Checked by snapshot only (`research/styles/_ko-regress/popcorn/`), not pixel-compared to skit 1.

1. `cp P/popcorn/popcorn.js code/props/popcorn.js`, `import './props/popcorn.js';` under the `// PROPS / INSERTS` marker in `code/index.html`.
2. `tools/prep.py` `EVENTS` row: `{"type":"popcorn","start":T,"slide":0.5,"turn_at":T+0.6,"turn":0.4}` (skit 1: start 31.64, turn_at 32.24). Put the bucket in a wide (A) or Ko (C) shot: it is at desk level beside Ko (x = Ko + 0.46 m), not visible in B.
3. SFX in `cues.src.json` `sfx`: `{"t":"popcorn.start","src":"swoosh-quick.mp3","db":-24}`, `{"t":"popcorn.start+0.36","src":"paper-crumple-quick.mp3","db":-21}`.
4. Optional cues: `ko_look` toward the bucket before `turn_at`.
5. Check: `bash tools/snap_sheet.sh <start+0.25>,<turn_at+0.4>,<turn_at+0.6>,<turn_at+1.3>`: bucket sliding in, Ko squashed / mid-hop turned right, landed and leaning back.
