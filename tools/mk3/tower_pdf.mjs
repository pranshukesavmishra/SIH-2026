// Plan Urena Tower: print the two HTML docs to PDF with Chromium.
//   node tools/mk3/tower_pdf.mjs      (needs Playwright; set CHROME=/path/to/chromium if it is not found)
import path from 'path'; import { fileURLToPath } from 'url'; import { createRequire } from 'module';
const require = createRequire(import.meta.url);
let pw; try { pw = require('playwright'); } catch (e) { pw = require('/opt/node22/lib/node_modules/playwright'); }
const HERE = path.dirname(fileURLToPath(import.meta.url));
const DOCS = path.join(HERE, 'tower/out/docs'), OUT = path.resolve(HERE, '../../docs/mk3');
const exe = process.env.CHROME || (require('fs').existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);
const b = await pw.chromium.launch({ executablePath: exe });
for (const [src, out] of [['pack.html', 'Plan_Urena_Tower.pdf'], ['shop.html', 'Plan_Urena_Tower_shop_sheet.pdf']]) {
  const p = await b.newPage();
  await p.goto('file://' + path.join(DOCS, src), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(OUT, out), format: 'A4', printBackground: true, margin: { top: '0', bottom: '0', left: '0', right: '0' }, preferCSSPageSize: true });
  console.log('wrote', out);
}
await b.close();
