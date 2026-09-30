// Plan Urena: print docs/mk3/plan.html and docs/mk3/print_shop.html to PDF with Chromium.
//   node tools/mk3/urena_pdf.mjs      (needs Playwright; set CHROME=/path/to/chromium if it is not found)
import path from 'path'; import { fileURLToPath } from 'url'; import { createRequire } from 'module';
const require = createRequire(import.meta.url);
let pw; try { pw = require('playwright'); } catch (e) { pw = require('/opt/node22/lib/node_modules/playwright'); }
const MK3 = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/mk3');
const exe = process.env.CHROME || (require('fs').existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);
const b = await pw.chromium.launch({ executablePath: exe });
const foot = t => `<div style="width:100%;font:7pt Helvetica,Arial;color:#8e8e93;padding:0 13mm;display:flex;justify-content:space-between">
  <span>${t} · internal</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;
for (const [src, out, t] of [['plan.html', 'Plan_Urena.pdf', 'Plan Urena'], ['print_shop.html', 'Plan_Urena_print_shop.pdf', 'Plan Urena · print shop']]) {
  const p = await b.newPage();
  await p.goto('file://' + path.join(MK3, src), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(MK3, out), format: 'A4', printBackground: true, displayHeaderFooter: true,
                headerTemplate: '<span></span>', footerTemplate: foot(t), margin: { top: '14mm', bottom: '16mm', left: '13mm', right: '13mm' } });
  console.log('wrote', out);
}
await b.close();
