#!/usr/bin/env python3
"""Build the 'still to buy' sheet from docs/data/bom_tier_a.json.

Generated, not hand-written, for the same reason the main BOM table is:
a hand-maintained copy of this list drifted once already. The rows come
from items flagged ``"status": "buy"`` in the BOM, plus an optional
``still_to_buy_extra`` block for anything not on the BOM at all.

Output: docs/submission/ZeroDrift_StillToBuy.pdf (via headless Chromium)
and the HTML it was rendered from, kept beside it so the PDF can be
regenerated or re-styled without this script.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOM = ROOT / "docs" / "data" / "bom_tier_a.json"
OUT_HTML = ROOT / "docs" / "submission" / "stilltobuy_source.html"
OUT_PDF = ROOT / "docs" / "submission" / "ZeroDrift_StillToBuy.pdf"

# Playwright's bundled Chromium; this environment has no system chrome.
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
)

CSS = """
  @page { size: A4; margin: 11mm 12mm; }
  * { box-sizing: border-box; }
  body { font-family: "DejaVu Sans", Arial, sans-serif; color: #15181c;
         font-size: 10pt; line-height: 1.38; margin: 0; }
  h1 { font-size: 17pt; margin: 0 0 1.5mm; letter-spacing: -0.3pt; }
  .sub { color: #5a6570; font-size: 9pt; margin: 0 0 4.5mm; }
  .total { background: #f2f5f8; border: 1px solid #d8e0e8; border-radius: 4px;
           padding: 3mm 3.5mm; margin: 0 0 4mm; font-size: 9.5pt; }
  .total b { font-size: 13pt; }
  .item { border: 1px solid #d8e0e8; border-radius: 5px; padding: 3mm 3.5mm;
          margin: 0 0 3mm; page-break-inside: avoid; }
  .head { display: flex; justify-content: space-between; align-items: baseline;
          gap: 4mm; margin-bottom: 2.5mm; }
  .name { font-weight: bold; font-size: 11.5pt; }
  .price { white-space: nowrap; color: #15181c; font-weight: bold; }
  .qty { display: inline-block; background: #15181c; color: #fff;
         border-radius: 3px; padding: 0.3mm 1.8mm; font-size: 9pt;
         margin-right: 2mm; }
  dl { margin: 0; display: grid; grid-template-columns: 20mm 1fr;
       gap: 1.4mm 3mm; }
  dt { font-size: 8.5pt; font-weight: bold; text-transform: uppercase;
       letter-spacing: 0.4pt; color: #5a6570; padding-top: 0.4mm; }
  dd { margin: 0; }
  .trap dt { color: #a11b1b; }
  .trap dd { color: #7d1414; }
  .foot { margin-top: 4mm; border-top: 1px solid #d8e0e8; padding-top: 3mm;
          font-size: 9pt; color: #5a6570; }
  .foot b { color: #15181c; }
"""


def rows(bom: dict) -> list[dict]:
    out = [it for sec in bom["sections"] for it in sec["items"]
           if it.get("status") == "buy"]
    out += bom.get("still_to_buy_extra", [])
    return out


def render_html(bom: dict) -> str:
    items = rows(bom)
    total = sum(it["qty"] * it["unit_inr"] for it in items)
    e = html.escape

    blocks = []
    for it in items:
        line = it["qty"] * it["unit_inr"]
        per = (f' &nbsp;<span style="color:#5a6570;font-weight:normal">'
               f'(₹{it["unit_inr"]:,} each)</span>' if it["qty"] > 1 else "")
        fields = [("Why", it.get("why", "")),
                  ("Check", it.get("check", ""))]
        dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in fields if v)
        trap = (f'<dl class="trap"><dt>Trap</dt><dd>{e(it["trap"])}</dd></dl>'
                if it.get("trap") else "")
        blocks.append(f"""
      <div class="item">
        <div class="head">
          <div class="name"><span class="qty">{it['qty']}&times;</span>{e(it['item'])}</div>
          <div class="price">₹{line:,}{per}</div>
        </div>
        <dl>{dl}</dl>{trap}
      </div>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>ZeroDrift Mk3 — still to buy</title><style>{CSS}</style></head>
<body>
  <h1>Still to buy</h1>
  <p class="sub">ZeroDrift Mk3 &middot; Team ZeroDrift, Jabalpur Engineering
     College &middot; SIH 2026, PS26169 (ISRO)</p>

  <div class="total">
    <b>₹{total:,}</b> outstanding across {len(items)} lines &mdash; everything
    else on the ₹{bom['total_inr']:,} bill of materials is already in hand.
    Generated from <code>docs/data/bom_tier_a.json</code>; do not hand-edit.
  </div>
  {''.join(blocks)}

  <div class="foot">
    <b>Before you glue anything:</b> the diametric magnets must say
    <b>DIAMETRIC</b>, not axial. The two look identical and an axial magnet
    makes an AS5600 read a constant &mdash; both feedback axes dead, with no
    error message. Test: spin one past a phone compass. The needle must flip
    twice per rotation. An axial magnet will not.<br><br>
    <b>And when you mount them:</b> each AS5600 chip sits <b>on the
    centreline</b> of the axis it measures, 1.5&nbsp;mm from the magnet face.
    Not near the axis &mdash; on it. Off-axis, the chip still answers on I²C
    and still returns numbers; they are simply not angles.
  </div>
</body></html>"""


def to_pdf(src: Path, dst: Path) -> None:
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        chrome = shutil.which("chromium") or shutil.which("google-chrome")
    if chrome is None:
        raise SystemExit("no Chromium available to print the PDF")
    subprocess.run(
        [chrome, "--headless", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", f"--print-to-pdf={dst}", src.as_uri()],
        check=True, capture_output=True)


def main() -> int:
    bom = json.loads(BOM.read_text())
    OUT_HTML.write_text(render_html(bom))
    to_pdf(OUT_HTML, OUT_PDF)
    items = rows(bom)
    total = sum(it["qty"] * it["unit_inr"] for it in items)
    print(f"{len(items)} lines, ₹{total:,} outstanding -> {OUT_PDF.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
