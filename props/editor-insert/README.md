# editor-insert

Full-screen empty code editor: «1» in the gutter, a blinking lime cursor, a mini Ko whose eyes blink with the cursor; slow zoom 1.00 -> 1.04 over the shot. Skit 1 shot S14. Ported to the insert contract (`../README.md`, section 2) as `editor.js`; checked by snapshot only.

1. `cp P/editor-insert/editor.js code/inserts/editor.js`, `import './inserts/editor.js';` under the `// PROPS / INSERTS` marker.
2. `tools/prep.py` `SHOTS` row `("S5","INSERT",start,{"ins":"editor"})`; no event needed. The shot runs to the next shot or to the end.
3. Edit `EDITOR` at the top of the file for another first line / caption position (`capTop`, default 700: caption stays on during the insert in the empty middle).
4. Check: `bash tools/snap_sheet.sh <start+0.2>,<start+0.7>` (cursor on / off, eyes open / blinking).
