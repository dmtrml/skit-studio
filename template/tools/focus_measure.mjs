// DoF blur radius (px at 1080 w, the shader's bsize) at the guy's head centre and Ko's face centre, every frame, per shot.
// usage: bash <gpu.sh> node tools/focus_measure.mjs [old|new] [OUT.txt]     (old = static focus points, for before/after)
// limits: guy in A/B <= ~1 px, Ko in C <= ~0.3 px (focus follows the head / Ko's face each frame).
import fs from 'node:fs';
import { PW, serve, launchArgs } from './paths.mjs';
const mode = process.argv[2] || 'new', outFile = process.argv[3] || 'focus.txt';
const pw = await import(PW);
const { srv, url } = await serve();
const browser = await pw.chromium.launch({ args: launchArgs });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
page.on('pageerror', e => console.log('pageerror', e.message));
if (mode === 'old') await page.addInitScript(() => { window.__FOCUS_OLD = true; });
await page.goto(url);
await page.waitForFunction(() => window.__focusBlur && window.__hf && window.__hf.buildReady, null, { timeout: 120000 });
await page.evaluate(() => window.__hf.buildReady['ko-skit']);
const rows = await page.evaluate(() => { const o = []; for (let f = 0; f < window.SKIT.frames; f++) o.push(window.__focusBlur(f / 30)); return o; });
const by = {};
for (const r of rows) { if (r.cam === 'INSERT') continue; (by[r.id] ||= { cam: r.cam, g: [], k: [] }); by[r.id].g.push(r.guy); by[r.id].k.push(r.ko); }
const st = a => [Math.max(...a), a.reduce((x, y) => x + y, 0) / a.length];
let out = `focus blur radius, px at 1080 w (${mode} focus). guy = head centre, ko = Ko face centre\nshot cam  guy_max guy_mean | ko_max ko_mean | frames\n`;
for (const id of Object.keys(by)) { const b = by[id], g = st(b.g), k = st(b.k); out += `${id.padEnd(4)} ${b.cam.padEnd(3)} ${g[0].toFixed(2).padStart(7)} ${g[1].toFixed(2).padStart(8)} | ${k[0].toFixed(2).padStart(6)} ${k[1].toFixed(2).padStart(7)} | ${b.g.length}\n`; }
const mx = (cams, key) => { const l = Object.values(by).filter(b => cams.includes(b.cam)); return l.length ? Math.max(...l.map(b => Math.max(...b[key]))).toFixed(2) : 'n/a'; };
out += `worst guy in A/B: ${mx(['A', 'B'], 'g')} px; worst Ko in C: ${mx(['C'], 'k')} px; worst Ko in A: ${mx(['A'], 'k')} px\n`;
fs.writeFileSync(outFile, out); console.log(out);
await browser.close(); srv.close();
