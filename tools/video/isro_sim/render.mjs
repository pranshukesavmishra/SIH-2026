// node render.mjs preview t1,t2,...   |   node render.mjs frames <start_s> <end_s> [workers]
import http from 'http'; import fs from 'fs'; import path from 'path'; import { chromium } from 'playwright-core';
const root = process.cwd(), types = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png' };
const srv = http.createServer((q, r) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html'; const f = path.join(root, p);
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(8793);
const [mode, a1, a2, a3] = process.argv.slice(2);
const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--ignore-gpu-blocklist', '--enable-gpu', '--use-angle=d3d11'] });
async function mk() { const p = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); }); p.on('pageerror', e => console.log('[err]', e.message));
  await p.goto('http://localhost:8793/index.html'); await p.waitForFunction('window.READY===true', null, { timeout: 180000 }); return p; }
if (mode === 'preview') { fs.mkdirSync('prev', { recursive: true }); const p = await mk();
  for (const t of a1.split(',')) { const s = Date.now(); await p.evaluate(t => seek(+t), t); await p.screenshot({ path: `prev/p_${t}.jpg`, type: 'jpeg', quality: 80 }); console.log(t, Date.now() - s, 'ms'); } }
else { const n0 = Math.round(+a1 * 30), n1 = Math.round(+a2 * 30), nw = +(a3 || 3); fs.mkdirSync('frames', { recursive: true });
  const pages = await Promise.all(Array.from({ length: nw }, mk)); let next = n0; const t0 = Date.now();
  await Promise.all(pages.map(async p => { for (;;) { const k = next++; if (k >= n1) break; const f = `frames/f${String(k).padStart(5, '0')}.jpg`;
    await p.evaluate(t => seek(t), k / 30); await p.screenshot({ path: f, type: 'jpeg', quality: 92 });
    if (k % 90 === 0) console.log('frame', k, 'of', n1, ((Date.now() - t0) / 1000).toFixed(0) + 's'); } })); }
await browser.close(); srv.close();
