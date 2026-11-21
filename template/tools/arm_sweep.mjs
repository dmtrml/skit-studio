// Evaluates window.__armClear(t) for every frame of code/ and prints min clearance (arms + held-prop corners vs torso/head) + its t.
// usage: bash <gpu.sh> node tools/arm_sweep.mjs     exit 0 when min clearance >= 0
import { PW, serve, launchArgs } from './paths.mjs';
const pw = await import(PW);
const { srv, url } = await serve();
const browser = await pw.chromium.launch({ args: launchArgs });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
page.on('pageerror', e => console.log('pageerror', e.message));
await page.goto(url);
await page.waitForFunction(() => window.__armClear && window.__hf && window.__hf.buildReady, null, { timeout: 90000 });
await page.evaluate(() => window.__hf.buildReady['ko-skit']);
const res = await page.evaluate(() => {
  let min = 9, at = 0; const bad = [];
  for (let f = 0; f < window.SKIT.frames; f++) { const t = f / 30, c = window.__armClear(t); if (c < min) { min = c; at = t; } if (c < 0) bad.push(f); }
  return { min, at, bad: bad.length, first: bad.filter((f, i) => i == 0 || f != bad[i - 1] + 1 || i == bad.length - 1) };
});
console.log(`min clearance ${res.min.toFixed(4)} m at t=${res.at.toFixed(2)} s; frames < 0: ${res.bad}`, res.first.join(','));
await browser.close(); srv.close();
process.exit(res.min >= 0 ? 0 : 1);
