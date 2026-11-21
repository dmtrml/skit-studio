# Characters from a picture (agent-facing)

The guy (human) and Ko (device) are built by `template/code/characters.js` from JSON passports in `template/characters/`. Rig, gestures, moods, mouth, focus, `poseGuy` do not depend on the passport. A new character = a new passport, no code.

Use (inside the skit folder — `template/` in this guide means the skit folder itself, so `template/characters/x.json` = `<skit>/characters/x.json`): put your own passport next to the others in `<skit>/characters/<name>.json` (copy `guy.json` or `woman_ref1.json` as a starting shape) and run `python characters/use.py <name>.json` from `<skit>` (the Ko passport defaults to `ko.json`; give a second argument only for another Ko, e.g. `ko_blue_round.json`). It writes `code/passport.js`. Then the usual `check` / `snap_sheet.sh mid`. No arguments = the original guy + Ko.

`woman_ref1.json` and `man_ref2.json` are **worked examples for two test pictures, not the answer for the person's picture** — never copy one as-is for a different picture; read the person's picture and write a new passport. In `top`, `pattern` (`none` or `plaid`), `color2` and `under` are optional: omit them for a plain top; `accent` is a single colour. A skirt or dress is not available: use the nearest `top` + `bottom` colours and tell the person. For a female character pick a female Gemini voice (SKILL step 3). Colours on the sheet look duller than in the picture: compare once and brighten the passport colour by ~10 % if needed.

## Passport (human)
`name, kind:"human", height 0.9–1.1, build slim|average|broad, skin #hex,`
`hair {style, color}, beard none|stubble|full, mustache none|thin|full|walrus, age young|adult|old, glasses none|round|square, headwear none|cap|beanie|hood,`
`top {type hoodie|tshirt|shirt|sweater|vest_over_shirt (color = the vest, shirt = the shirt colour under it; sleeves take the shirt colour), color, pattern none|plaid, color2 (plaid 2nd colour), under (shirt: undershirt strip colour)},`
`bottom {color}, shoes #hex, accent #hex (drawstrings, cap brim, bun/ponytail tie), headphones bool,`
`age: old` turns hair, brows, beard and mustache grey (a light tint over `hair.color`; a bald old man: `hair.style none`, `hair.color` any grey); `young` and `adult` change nothing. Posture does not change with age (the rig stays untouched) — say so if asked. `mustache` uses `beard_color` (or the hair colour).
`face {brow_color, eye_color, mouth_color, freckles bool, head_size 0.9–1.05, glasses_color, beard_color, headwear_color}`
Hair styles: `none` (bald), `buzz`, `short`, `messy` (the original guy), `side_part`, `long`, `curly`, `bun`, `curly_bun`, `ponytail`, `cap_covered` (only back/side hair showing under a hat; any style other than none/long/ponytail is switched to it when `headwear` is set).
Device: `{ name, kind:"device", body {shape block|round|sharp|wide|slim, color}, screen_face true, outline 0.5–2 }`; the colour drives the shade/highlight palette, the `happy` glow and the sparks.

## Reading a picture
1. Look at the picture at full size once. Fill in order: build (shoulder width vs head), skin (the lit mid-tone of the cheek, not a shadow), hair style + colour, headwear, glasses, beard, top (type, colour, pattern), bottom, shoes. Hex from what you see; keep the saturation of the picture, lighting will darken it.
2. Top type: pullover with hood = hoodie; knit/crew = sweater; collar + buttons or open over a tee = shirt (+ `under`); short sleeves = tshirt. Plaid/checks = `pattern:"plaid"` + `color`, `color2`.
3. Cartoon vs photo: same fields; a cartoon's flat colour is the colour, a photo's is the mid-tone.
4. Female/male is not a field. It reads through hair, build (`slim`), head_size ~0.95, glasses, lips (`mouth_color` warmer), freckles. Check the sheet: if she still reads as the default guy recoloured, change hair first, then build.

## Ask the person when the picture does not say
- Hair from behind or under a hat (length, colour). Eye colour when closed/dark. Whether a beard is stubble or full. Clothes cut off by the frame (bottoms, shoes). Exact skin tone when the photo is strongly tinted. Whether headphones are wanted (default off for new characters).
- Do not ask about things a stylised box head cannot show (nose shape, ears, wrinkles).

## Limits
Stylised, not a copy. Recognisable by silhouette (build, hair mass, hat), colour blocks (top/bottom/skin/hair) and 2–3 details (glasses, beard, freckles, plaid). Not available: faces' exact proportions, tattoos, jewellery, logos, skirts/dresses (the guy sits at a desk in trousers), side-by-side characters other than guy + Ko. Hair is volumes of rounded boxes/spheres; curls are spheres, not strands. Plaid is a texture on the soft look only. Beard + mouth: the mouth moves in front of the beard.
Extending: new hair/headwear = one branch in `buildGuy` (hair parts are children of `head`, keep them inside ±0.25 of the head centre so the arm clearance model holds); then re-run the checks below on every passport.

## Checks per passport (all in `template/tools/`, through gpu.sh)
`check` 0 errors; `node tools/arm_sweep.mjs` min clearance ≥ 0 (height/build change the torso box and shoulders; they are exported from `buildGuy` to the clearance model); `node tools/focus_measure.mjs` guy head blur ≈ 0 in A/B; `python tools/face_luma.py <B-shot times>` max ≤ 241 (light skin is the risk); one `snap_sheet.sh mid` sheet looked at.

## Cost of a new character
Passport from a clear picture ≈ 5–10 min and ~30–60k tokens (one look + one sheet); one correction round (hair/colours) ≈ +5 min. Checks ≈ 6–8 min of machine time, no tokens. New hair style/headwear/top type (code) ≈ 1 builder round.
Verified on `template/characters/woman_ref1.json` (cartoon: curly bun, round glasses, sweater) and `man_ref2.json` (photo: beanie, full beard, plaid shirt over tee).

## What the passport cannot do (say it to the person BEFORE the first sheet, one line; list again under the sheet what did not come out)

| Wish | Not available | Nearest workaround |
|---|---|---|
| Skirt / dress | no | `top` + `bottom` colours of the dress |
| Tie, scarf, jewellery, hat other than cap/beanie/hood | no | nearest `accent` colour; say it |
| Waistcoat with a different cut, jacket, coat | only `vest_over_shirt` | `shirt`/`sweater` in the jacket colour |
| Bent posture of an old person | no (rig is shared) | `age: old`, `height 0.97`, `build slim` |
| Wrinkles, specific face shape | no | `age: old` greys the hair and brows |
| Moustache styles beyond thin / full / walrus | no | the nearest one |

Worked example of an old man: `characters/old_man.json` (bald, grey walrus mustache, round glasses, vest over a shirt) — a sample, not the answer for another description. Sheet of the hero without the template's demo subtitles: `bash tools/snap_sheet.sh hero`.
