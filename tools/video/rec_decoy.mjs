import pkg from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pkg;
import fs from 'fs';
const [t0, t1, out] = [85.6, 95.6, 'frames_decoy'];
fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.8 });
await p.goto('http://localhost:8791/console.html', { waitUntil: 'networkidle' });
await p.waitForFunction(() => typeof D !== 'undefined' && D && D.frames && D.frames.length > 3000);
const info = await p.evaluate(([t0, t1]) => {
  playing = false; document.getElementById('debrief').hidden = true; window.__vt = 0; performance.now = () => window.__vt;
  const a = D.frames.findIndex(f => f.t >= t0), z = D.frames.findIndex(f => f.t >= t1);
  return [a, z, D.scenario, D.frames[a].t, D.frames[z].t];
}, [t0, t1]);
console.log(info);
const [a, z] = info;
await p.evaluate(a => { for (let j = a - 60; j < a; j++) { window.__vt = j * 1000 / 30; i = j; draw(); } }, a);
for (let k = a; k < z; k++) {
  await p.evaluate(k => { playing = false; window.__vt = k * 1000 / 30; i = k; ph = k; frac = 0; draw(); }, k);
  await p.screenshot({ path: `${out}/f${String(k - a).padStart(4, '0')}.png` });
}
console.log('frames', z - a);
await b.close();
