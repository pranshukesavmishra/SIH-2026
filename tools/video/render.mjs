// node render.mjs <scene> <seconds> <outdir> [query] [alpha]  |  node render.mjs preview <scene> <t1,t2,..> [query]
import pkg from '/opt/node22/lib/node_modules/playwright/index.js'; const { chromium } = pkg;
import fs from 'fs';
const a = process.argv.slice(2);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const base = 'file://' + process.cwd() + '/motion/motion.html?';
if (a[0] === 'preview') {
  await p.goto(base + 'scene=' + a[1] + '&' + (a[3] || '')); await p.evaluate(() => document.fonts.ready);
  for (const t of a[2].split(',')) { await p.evaluate(t => seek(+t), t); await p.screenshot({ path: `prev_${a[1]}_${t}.png`, omitBackground: ['tag','lockfx','hud'].includes(a[1]) }); }
} else {
  const [scene, secs, out, qs, alpha] = a; fs.mkdirSync(out, { recursive: true });
  await p.goto(base + 'scene=' + scene + '&' + (qs || '')); await p.evaluate(() => document.fonts.ready);
  const n = Math.round(+secs * 30);
  for (let k = 0; k < n; k++) { await p.evaluate(t => seek(t), k / 30);
    await p.screenshot({ path: `${out}/f${String(k).padStart(4, '0')}.png`, omitBackground: alpha === '1' }); }
  console.log(scene, n, 'frames');
}
await b.close();
