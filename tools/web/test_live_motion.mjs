import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { readFileSync } from 'fs';
// Usage:  cd docs && python3 -m http.server 8099 &
//         node ../tools/web/test_live_motion.mjs /tmp
// Drives the REAL live.html in headless Chromium with a synthetic camera
// (fake_cam.js): static acquisition, two fast sweeps with a direction
// reversal, a steady decoy lamp. Verifies lock, motion tracking, honest
// coasting, decoy rejection and a sane margin readout.
const S = process.argv[2] || '/tmp';
const HERE = new URL('.', import.meta.url).pathname;
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
const pg = await b.newPage({ viewport: { width: 1100, height: 850 } });
pg.on('pageerror', e => console.log('PAGEERROR', String(e).slice(0, 200)));
await pg.addInitScript(readFileSync(`${HERE}/fake_cam.js`, 'utf8'));
await pg.goto('http://127.0.0.1:8099/live.html');
await pg.click('#startBtn');

const samples = [];
const t0 = Date.now();
while (Date.now() - t0 < 14500) {
  const s = await pg.evaluate(() => {
    const tr = window.__truth();
    return { ds: displayState(), st: state, p: pos ? [pos.x, pos.y] : null,
             m: margin, v: [vel.x, vel.y],
             tt: tr ? tr.t : null, tp: tr ? tr.p : null };
  });
  samples.push(s);
  await new Promise(r => setTimeout(r, 100));
}
await pg.screenshot({ path: `${S}/live_motion_end.png` });
await b.close();

const fail = [], ok = m => console.log('  ok:', m);
const err = s => s.p && s.tp ? Math.hypot(s.p[0]-s.tp[0], s.p[1]-s.tp[1]) : 1e9;
const inWin = (a,b) => samples.filter(s => s.tt >= a && s.tt < b);

// 1. locked on the beacon before the first sweep
const pre = inWin(3.2, 4.4).filter(s => s.st === 'LOCKED');
if (!pre.length) fail.push('no LOCKED before first sweep');
else {
  const e = Math.min(...pre.map(err));
  e < 30 ? ok(`locked pre-sweep, err ${e.toFixed(0)}px`) : fail.push(`pre-sweep lock err ${e.toFixed(0)}px`);
}
// 2. through sweep 1 (4.5-5.7s): never SEARCHING, tracking error bounded
const sw1 = inWin(4.6, 5.8);
if (sw1.some(s => s.st === 'SEARCHING')) fail.push('dropped to SEARCHING during sweep 1');
else ok('no SEARCHING during sweep 1');
const sw1e = sw1.map(err);
const held1 = sw1e.filter(e => e < 70).length / Math.max(sw1e.length, 1);
held1 >= 0.7 ? ok(`sweep-1 ring within 70px for ${(held1*100)|0}% of samples`)
             : fail.push(`sweep-1 tracking held only ${(held1*100)|0}% (errs ${sw1e.map(e=>e|0).join(',')})`);
// 3. settled after sweep 1
const set1 = inWin(7.0, 8.8).filter(s => s.st === 'LOCKED' && err(s) < 30);
set1.length ? ok('re-settled LOCKED at sweep-1 endpoint') : fail.push('no settled lock at (240,90)');
// 4. through sweep 2 and final settle
const sw2 = inWin(9.1, 10.0);
if (sw2.some(s => s.st === 'SEARCHING')) fail.push('dropped to SEARCHING during sweep 2');
else ok('no SEARCHING during sweep 2');
const set2 = inWin(11.5, 14.0).filter(s => s.st === 'LOCKED' && err(s) < 30);
set2.length ? ok('re-settled LOCKED at final position') : fail.push('no settled lock at (120,170)');
// 5. never on the steady lamp
const lamp = samples.find(s => s.st === 'LOCKED' && s.p && Math.hypot(s.p[0]-270, s.p[1]-200) < 35);
lamp ? fail.push(`locked the STEADY lamp at t=${lamp.tt?.toFixed(1)}s`) : ok('steady lamp never captured');
// 6. margin sane
const mx = Math.max(...samples.map(s => s.m));
mx <= 60 ? ok(`margin bounded (max ${mx.toFixed(1)}x)`) : fail.push(`margin absurd: ${mx}`);
// 7. velocity engaged during sweeps
const vmax = Math.max(...samples.map(s => Math.hypot(s.v[0], s.v[1])));
vmax > 1.5 ? ok(`velocity feed-forward engaged (peak ${vmax.toFixed(1)} px/f)`)
           : fail.push(`velocity never engaged (${vmax.toFixed(2)})`);

console.log(fail.length ? '\nFAILURES:\n  - ' + fail.join('\n  - ') : '\nALL MOTION CHECKS PASSED');
process.exit(fail.length ? 1 : 0);
