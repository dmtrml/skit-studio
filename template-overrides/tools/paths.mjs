// import { SKIT, ROOT, PW, serve, launchArgs } from './paths.mjs'
// PW = playwright module URL (installed by /skit-studio:setup into ~/.skit-studio/node_modules; env SKIT_PLAYWRIGHT overrides)
// serve(codeDir) = static server for code/
import fs from 'node:fs'; import http from 'node:http'; import os from 'node:os'; import path from 'node:path'; import { fileURLToPath, pathToFileURL } from 'node:url';
export const SKIT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ROOT = SKIT;
export const PW = pathToFileURL(process.env.SKIT_PLAYWRIGHT || path.join(os.homedir(), '.skit-studio', 'node_modules', 'playwright', 'index.mjs')).href;
if (!fs.existsSync(fileURLToPath(PW))) throw new Error('paths.mjs: playwright not found at ' + fileURLToPath(PW) + ' (run /skit-studio:setup)');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wav': 'audio/wav', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.png': 'image/png' };
export async function serve(dir = path.join(SKIT, 'code')) {
  const srv = http.createServer((q, s) => {
    const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]).replace(/^\/$/, '/index.html'));
    fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); s.end(d); } });
  });
  await new Promise(res => srv.listen(0, '127.0.0.1', res));
  return { srv, url: `http://127.0.0.1:${srv.address().port}/index.html` };
}
export const launchArgs = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
