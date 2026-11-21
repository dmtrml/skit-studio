# Ko skit: props and inserts (plug-in contract + how-to)

Agent-facing, English. The base look (`template/code/index.html`) has no prop and no insert in it. A skit that needs a phone, a chat screen, popcorn, an editor window plugs them in with one `import` line each (never a `<script src>` tag, see the pitfall below). Everything per-skit is data: `timeline.json` (`TL`, from `tools/prep.py`) and `cues.json` (`CU`, from `cues.src.json` via `tools/cues.py`).

## 1. Prop contract (3D objects, poses, gaze, light)

File `code/props/<name>.js`. Load it under the `// PROPS / INSERTS` comment in the module script of `code/index.html`: one side-effect line `import './props/x.js';` (the same marker serves inserts).
It registers one object: `window.KO_PROPS = window.KO_PROPS || {}; window.KO_PROPS.<name> = { ...hooks };`. All hooks are optional, all get the shared context `c` (`KX` in index.html).

| Hook | Called | Does |
|---|---|---|
| `build(c)` | once, after the guy, arms, Ko and the base POSE table exist | create meshes (`c.obj`, `c.put`, `c.RB`, `c.BX`, `c.CY`, `c.SP`, `c.glowMat`, `c.PAL`), attach to `c.arms[i].hand`, `c.koG`, `c.scene`, `c.GUY`, `c.LAP`; add lights; keep state in the closure |
| `poses(c)` | once, after every `build` | return `{ poseName: s => ({ p, fd, pn, curl, idx, pole }) }`, merged into the arm POSE table; `s` = -1 for arm 0 (L hand), +1 for arm 1 (R hand); `p` wrist target and `pole` elbow hint in `up` space, `fd` finger direction, `pn` palm normal, `curl` 0..1, `idx` index finger shown 0/1. Gesture type in `cues.src.json` = the pose name, `side` picks the hand |
| `armBase(i, t, c)` | every frame per arm | the resting pose of arm `i` instead of the keyboard (return a pose object, or null). While non-null the hand does not dip with typing keys. Gestures blend over it |
| `lookTargets(c)` | once | return `{ name: { yaw, pitch } }`; `yaw` = head yaw (rad, from `c.yawTo(worldPoint)`), `pitch` = extra head pitch. Enables `look: [{at: "name"}]` in cues |
| `handPoints(i, c)` | once | hand-local points (array of `c.V`) of an object held by arm `i`: used by the arm-vs-body clearance solver and by `tools/gesture_frame.mjs` (must stay inside the frame) |
| `koFx(t, ko, c)` | every frame, after all Ko effects | `ko = { sx, sy, by, rotY, rotX }` (squash x/y, lift m, yaw, pitch of the Ko body); modify in place (multiply `sx`/`sy`, add to `by`/`rotX`/`rotY`); the base applies it. For hops, turns, squashes |
| `update(t, shot, c)` | every frame, after the base light/atmosphere update | pure function of `t`: light tweaks (e.g. `c.keySpot.intensity *= ...`), visibility, texture redraw |

Context `c` (selection): `THREE, scene, cam, renderer, V, obj, put, link, RB, BX, CY, SP, glowMat, PAL, COMIC, dpr, INK, LIME, clamp, seg, out3, backOut, rmsAt, TL, CU, W, H, up` (guy's upper body group; wrist targets live in this space), `head, arms[0|1]` (`.hand .fing .idx`), `GUY, LAP, lid, koG, KD` (Ko direction in `up` space), `Y, handRest[i], qFP(fd, pn), yawTo, YAW_KO, YAW_SCR, CAMS, POSE, lookW(t, name), gMax(t, who, type, i), gAmp, keySpot, FILL, FOCUS`.

**Pitfall (found 10.11):** load props/inserts with `import` in the module script, NEVER with a `<script src>` tag in the HTML: the HyperFrames compiler inlines classic local scripts into the page and mangles them (a 5 KB script showed up as visible text and pushed the whole frame down; HTML-looking template strings became real DOM). Imported modules (like `look3.js`) are left alone. Still build DOM with `document.createElement`, not HTML strings (see `chat.js`, `editor.js`).

**Pitfall 2 (fonts):** HyperFrames embeds Roboto in place of 'Segoe UI' only if the HTML has a `font-family:` LONGHAND declaration naming it (the `font:` shorthand is not scanned). The base keeps `font-family:"Segoe UI"` on `#ins` for this; without it the caption renders in the system Segoe UI and no longer matches skit 2 (frame diff 3.3 instead of 0.07). Do not remove it.

Rules: pure function of `t` (seek-safe, no accumulated state, no `Math.random` without a fixed seed); skit data only from `TL` / `CU`; no per-frame allocation of textures.

## 2. Insert contract (full-screen DOM screens)

File `code/inserts/<name>.js`, an `import './inserts/x.js';` line under the same `// PROPS / INSERTS` marker.
`window.KO_INSERTS = window.KO_INSERTS || {}; window.KO_INSERTS.<name> = { init(el, c), draw(t, shot, ev, c), capTop? }`.
- `init(el, c)`: once at load; `el` = your own full-frame (1080x1920) wrapper inside `#ins`; build DOM/CSS in it (set `el.style.background`). Do not measure layout here.
- `draw(t, shot, ev, c)`: every frame while a shot with `cam: "INSERT"` and `ins: "<name>"` is on (fallback: the first `TL.events` entry whose `type` is a registered insert and has started). `ev` = the `TL.events` row with `type === name` (or null); other events via `c.TL.events`. Pure function of `t`. The base shows `#ins`, hides the other inserts and does not render 3D during an insert.
- `capTop` (px, default 1640): where the caption sits during the insert (captions stay on). Keep this zone empty.
Shots and events come from `tools/prep.py` tables `SHOTS` / `EVENTS`; cue times can refer to event numbers: `"chat1.reply+0.1"` in `cues.src.json`.

## 3. Sound

`sound/mix.py` places `cues.sfx = [{t, src, db, dur?}]`: `src` = a file in `sound/src/` or a synth preset `ding | tick | pop | limit`; `db` = peak dBFS; `dur` = keep only the first seconds (soft fade). Props below list the SFX they expect.

## 4. Props library (copy what the skit needs; this folder is not copied automatically)

Paths below are relative to the skit folder; `P` = `<plugin>/props`.

### phone (`P/phone/phone.js`)
Phone in the guy's L hand: mesh with a chat-like screen, poses `hold_phone` (automatic resting base of arm 0), `show_phone` (screen toward Ko and camera A), `lower_phone` (back to the lap); `look.at: "phone"`; cold screen light on the face; key light dims 35 % while he looks at the phone; 8 box corners feed the arm clearance and the framing check.
1. `cp P/phone/phone.js code/props/phone.js` (create `code/props/`), add `import './props/phone.js';` under the `// PROPS / INSERTS` marker.
2. `cues.src.json`: gestures `{"type":"show_phone","side":"L","t":...,"end":...}` and `lower_phone` (same hand, `side: "L"`); `look`: `{"start":-1,"end":"L1.s+0.3","at":"phone"}`. Skit 2 values: `research/styles/ko-skit-2-plus1/cues.src.json`.
3. Needs no SFX. Typing cues keep working for the other hand.
4. Checks: `bash $G node tools/arm_sweep.mjs` (min clearance >= 0, includes the phone corners), `bash $G node tools/gesture_frame.mjs` (phone corners inside .02-.98 in B shots), `python tools/hand_luma.py` for blown-out hands.

### chat-insert (`P/chat-insert/chat.js`)
Dark dating-app chat: `chat1` = the green sent bubble pops, the chat scrolls up, the grey reply pops (with «дзынь»); `chat2` = zoom on the reply, a lime highlighter wipes over one word of it. All texts are the `CHAT_TEXT` object at the top of the file: name, avatar letter, status, history bubbles (`g` ours / `h` hers, text, time), the sent bubble, the reply split in `before / hl / after`. Edit text only.
1. `cp P/chat-insert/chat.js code/inserts/chat.js` (create `code/inserts/`), add `import './inserts/chat.js';` under the same marker.
2. `tools/prep.py`: `SHOTS` rows `("S5","INSERT",i1,{"ins":"chat1"})` and `("S8","INSERT",x,{"ins":"chat2"})`; `EVENTS` rows `{"type":"chat1","start":i1,"sent":i1+0.35,"reply":i1+0.95}` and `{"type":"chat2","start":x,"mark":m}`. Leave a pause in `LINES` for the insert (skit 2: 3.15 s before «Она ответила за две секунды.»; the sent bubble pops 0.35 s into the insert, the reply 0.6 s later).
3. SFX in `cues.src.json` `sfx`: `{"t":"chat1.sent","src":"swoosh-quick.mp3","dur":0.18,"db":-30}`, `{"t":"chat1.reply","src":"ding","db":-20}`, `{"t":"chat2.mark","src":"tick","db":-32}`.
4. Checks: `bash tools/snap_sheet.sh <t during chat1 before sent>,<after reply>,<chat2 after mark>` and look at the sheet: bubbles not clipped, caption below the chat, dash highlighted.

### popcorn (`P/popcorn/popcorn.js`, details `P/popcorn/README.md`)
Striped bucket slides to Ko at desk level; Ko squashes, hops, turns, lands, leans back (hooks `build`, `update`, `koFx`). Ported from skit 1; snapshot-checked only.
1. `cp P/popcorn/popcorn.js code/props/popcorn.js` + `import './props/popcorn.js';` under the marker.
2. `tools/prep.py` `EVENTS`: `{"type":"popcorn","start":T,"slide":0.5,"turn_at":T+0.6,"turn":0.4}`; show it in an A or C shot.
3. SFX: `{"t":"popcorn.start","src":"swoosh-quick.mp3","db":-24}`, `{"t":"popcorn.start+0.36","src":"paper-crumple-quick.mp3","db":-21}`.
4. Check: `bash tools/snap_sheet.sh <start+0.25>,<turn_at+0.4>,<turn_at+0.6>,<turn_at+1.3>`.

### editor-insert (`P/editor-insert/editor.js`, details `P/editor-insert/README.md`)
Empty code editor «1», blinking cursor, mini Ko blinking with it (skit 1, shot S14). Ported cleanly as an insert; snapshot-checked only.
1. `cp P/editor-insert/editor.js code/inserts/editor.js` + `import './inserts/editor.js';` under the marker.
2. `tools/prep.py` `SHOTS`: `("S5","INSERT",start,{"ins":"editor"})`. Edit the `EDITOR` object (first line, `capTop`) in the file.
3. Check: `bash tools/snap_sheet.sh <start+0.2>,<start+0.7>`.

### notify-insert (`P/notify-insert/notify.js`, skit 3 «Как сын»)
The guy's laptop screen: a browser window with a search query in the bar and as the page heading (a joke callback), then a desktop notification pops in from the top (mini Ko app icon that blinks, sender, text). Texts in `NOTIFY` at the top (`query: ''` hides the browser). Slow zoom 1.00 → 1.04 over the shot.
1. `cp P/notify-insert/notify.js code/inserts/notify.js` + `import './inserts/notify.js';` under the marker.
2. `tools/prep.py`: `SHOTS` row `("S15","INSERT",i1,{"ins":"notify"})`; `EVENTS` row `{"type":"notify","start":i1,"pop":i1+0.45}`. After the last line: `TAIL` must cover the gap + insert + the wide tail (skit 3 `tools/prep.py`).
3. SFX: `{"t":"notify.pop","src":"ding","db":-20}`.
4. Check: `bash tools/snap_sheet.sh <start+0.2>,<pop+0.3>,<end-0.2>`: toast text on 2 lines max, not clipped.

### endcard (`P/endcard/endcard.js`, skit 3)
Closing end card OVER the running 3D scene (a prop, not an insert, so the room keeps playing): CSS blur + darkening on the `#gl` canvas over 0.6 s, a title pops at the top («Этот скетч целиком сделан в Claude»), the CTA box pops at the bottom («Напиши „КО“ в комментах…»). Texts in `END`; font = `assets/fonts/impact.ttf` via @font-face (renders in HF 0.9.31).
1. `cp P/endcard/endcard.js code/props/endcard.js` + `import './props/endcard.js';` under the marker.
2. `tools/prep.py` `EVENTS`: `{"type":"endcard","start":T,"cta":T+0.6}` inside the last wide shot; extend `TAIL` by ≈ 2.7 s (skit 3: card from 1.8 s into the tail, 2.7 s long). No caption line may overlap it.
3. Check: `bash tools/snap_sheet.sh <start-0.1>,<start+0.3>,<cta+0.2>,<end-0.2>`.
