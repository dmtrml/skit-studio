// prints {"t": [[x,y] of both hands]} (normalised) for the given times as JSON, for tools/hand_luma.py (keys = snapshot times)
// usage: bash <gpu.sh> node tools/hand_boxes.mjs 5.2 12.4 22.2 > hands.json
import { PW, serve, launchArgs } from './paths.mjs';
const pw = await import(PW);
const { srv, url } = await serve();
const browser = await pw.chromium.launch({ args: launchArgs });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
await page.goto(url);
await page.waitForFunction(() => window.__handScreen, null, { timeout: 90000 });
const ts = process.argv.slice(2), out = {};
for (const t of ts) { const r = await page.evaluate(t => window.__handScreen(t), +t); out[t] = r.hands.map(h => h.xy); }
console.log(JSON.stringify(out));
await browser.close(); srv.close();
