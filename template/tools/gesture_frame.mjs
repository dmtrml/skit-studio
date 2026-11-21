// Framing check: at each guy arm-gesture hold midpoint (B shots) every gesturing hand must be inside x .10-.90, y .35-.92
// and >= .12 frame width from the face centre (except rub_eyes). Held-prop corners (props with handPoints, e.g. phone) must stay in .02-.98.
// Gesture types checked = every arm pose the page knows (window.__ARMT, incl. prop poses) minus the resting hold_*.
// usage: bash <gpu.sh> node tools/gesture_frame.mjs
import fs from 'node:fs'; import path from 'node:path';
import { SKIT, PW, serve, launchArgs } from './paths.mjs';
const pw = await import(PW);
const { srv, url } = await serve();
const browser = await pw.chromium.launch({ args: launchArgs });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
page.on('pageerror', e => console.log('pageerror', e.message));
await page.goto(url);
await page.waitForFunction(() => window.__handScreen && window.__ARMT, null, { timeout: 90000 });
const cues = JSON.parse(fs.readFileSync(path.join(SKIT, 'cues.json'), 'utf8'));
const ARM = (await page.evaluate(() => window.__ARMT)).filter(n => !/^hold_/.test(n));
let fail = 0;
const f2 = v => v.toFixed(2);
for (const g of cues.gestures.filter(g => g.who === 'guy' && ARM.includes(g.type))) {
  const t = +(g.t + g.dur / 2).toFixed(3);
  const r = await page.evaluate(t => window.__handScreen(t), t);
  const hs = r.hands.filter(h => h.w > .5);
  if (r.cam !== 'B') { console.log(`skip ${g.type} t=${t} cam ${r.cam}: ${hs.map(h => h.xy.map(f2)).join(' | ')}`); continue; }
  if (r.props && r.props.length) { const px = r.props.map(c => c[0]), py = r.props.map(c => c[1]), pin = Math.min(...px) >= .02 && Math.max(...px) <= .98 && Math.min(...py) >= .02 && Math.max(...py) <= .98;
    if (!pin) fail++; console.log(`${pin ? 'OK  ' : 'FAIL'} prop t=${t} cam=${r.cam} x ${f2(Math.min(...px))}-${f2(Math.max(...px))} y ${f2(Math.min(...py))}-${f2(Math.max(...py))}`); }
  for (const h of hs) {
    const [x, y] = h.xy, dist = Math.hypot(x - r.face[0], (y - r.face[1]) * 16 / 9);   // in frame widths
    const ok = x >= .10 && x <= .90 && y >= .35 && y <= .92 && (g.type === 'rub_eyes' || dist >= .12);
    if (!ok) fail++;
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${g.type} t=${t} hand${h.i} x=${f2(x)} y=${f2(y)} face=(${r.face.map(f2)}) dist=${f2(dist)}`);
  }
}
await browser.close(); srv.close(); process.exit(fail ? 1 : 0);
