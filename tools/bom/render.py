"""
Render every copy of the BOM from docs/data/bom_tier_a.json.

The JSON has always claimed to be the single source of truth, and
tests/test_bom_consistency.py has always enforced that the copies agree
with it -- but the copies were still edited by hand, so "generated from
this" was aspirational. Every price correction meant editing the same
numbers in three places and hoping. It went wrong once already: the BOM
summed to Rs 5,944 while stating Rs 6,124 and the printed guide said Rs
6,331, three different answers to what a student should take to the shop.

    python tools/bom/render.py          rewrite the markdown table and
                                        the buy-list HTML in place

The PDFs are produced from the HTML separately; this writes the sources
they come from.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data" / "bom_tier_a.json"
DOC = ROOT / "docs" / "TERMINAL_MK3.md"
BUYLIST = ROOT / "docs" / "submission" / "buylist_checklist_source.html"
GUIDE = ROOT / "docs" / "submission" / "build_guide_source.html"

BASIS_LABEL = {"verified": "✅ verified", "estimate": "~ estimate",
               "reuse Mk1": "reuse Mk1"}


def load():
    bom = json.loads(DATA.read_text(encoding="utf-8"))
    total = sum(i["qty"] * i["unit_inr"] for s in bom["sections"] for i in s["items"])
    if total != bom["total_inr"]:
        raise SystemExit(f"bom_tier_a.json states ₹{bom['total_inr']:,} but its "
                         f"items sum to ₹{total:,}; fix the data, not the render")
    return bom


def markdown_table(bom) -> str:
    rows = ["| Item | Qty | Unit | Total | Price basis |", "|---|---|---|---|---|"]
    for s in bom["sections"]:
        rows.append(f"| **{s['title']}** | | | | |")
        for i in s["items"]:
            sub = i["qty"] * i["unit_inr"]
            basis = BASIS_LABEL.get(i["price_basis"], i["price_basis"])
            if i["qty"] == 0:
                qty, unit = "—", "—"
            else:
                qty, unit = str(i["qty"]), f"₹{i['unit_inr']:,}"
            rows.append(f"| {i['item']} | {qty} | {unit} | **₹{sub:,}** | {basis} |")
    rows.append(f"| **TOTAL** | | | **₹{bom['total_inr']:,}** | |")
    return "\n".join(rows)


def rewrite_markdown(bom) -> bool:
    doc = DOC.read_text(encoding="utf-8")
    # The table is delimited by its own header row and the first blank line
    # after it, which is how it has always been laid out in this document.
    start = doc.index("| Item | Qty | Unit | Total | Price basis |")
    end = doc.index("\n\n", start)
    new = doc[:start] + markdown_table(bom) + doc[end:]
    if new == doc:
        return False
    DOC.write_text(new, encoding="utf-8")
    return True


def rewrite_buylist(bom) -> bool:
    """
    Rewrite the one-page buy list's table and every total on it.

    Routing (Amar Robotics / Blinkit / Online) now lives in the JSON
    alongside the price, because it could not be regenerated while it
    lived only in the HTML -- adding an item meant hand-editing a row
    and hand-adding three column subtotals, which is exactly the class
    of arithmetic that had the BOM disagreeing with itself three ways.
    """
    if not BUYLIST.exists():
        return False
    html = BUYLIST.read_text(encoding="utf-8")
    start = html.index("<tbody>") + len("<tbody>")
    end = html.index("</tbody>")

    cols = ("amar", "blinkit", "online", "have")
    subtotal = {c: 0 for c in cols}
    rows = []
    for s in bom["sections"]:
        for i in s["items"]:
            sub = i["qty"] * i["unit_inr"]
            src = i.get("source", "amar")
            subtotal[src] = subtotal.get(src, 0) + sub
            qty = "—" if i["qty"] == 0 else str(i["qty"])
            tick = "✓" if i["price_basis"] == "verified" else "~"
            cells = "".join(
                f'<td class="ck{" yes" if c == src else ""}{" online-col" if c == "online" else ""}">'
                f'{"&#10003;" if c == src else ""}</td>' for c in cols)
            rows.append(f'<tr><td class="q">{qty}</td><td>{i["item"]}</td>'
                        f'<td class="p">{tick}</td><td class="v">₹{sub:,}</td>{cells}</tr>')

    rows.append(f'<tr class="totrow"><td></td><td>GRAND TOTAL</td><td></td>'
                f'<td class="v">₹{bom["total_inr"]:,}</td>'
                + "".join(f'<td class="ck{" online-col" if c == "online" else ""}">'
                          f'₹{subtotal[c]:,}</td>' for c in cols) + "</tr>")

    body = "\n" + "\n".join(rows) + "\n"
    new_html = html[:start] + body + html[end:]
    # The headline total appears once more, in the subtitle.
    new_html = re.sub(r"Total ₹[\d,]*\d", f"Total ₹{bom['total_inr']:,}", new_html)
    if new_html == html:
        return False
    BUYLIST.write_text(new_html, encoding="utf-8")
    return True


def rewrite_guide(bom) -> bool:
    """
    Rewrite the printed build guide's BOM table and its two totals.

    This one is the document a student actually carries to the shop, so
    it is the copy that must never be stale -- and it was the copy that
    went stale, printing Rs 6,331 against a BOM of Rs 6,124.
    """
    if not GUIDE.exists():
        return False
    html = GUIDE.read_text(encoding="utf-8")
    tag = {"verified": '<span class="tag v">&#10003; verified</span>',
           "estimate": '<span class="tag e">~ estimate</span>',
           "reuse Mk1": '<span class="tag r">reuse Mk1</span>'}

    rows = []
    for sec in bom["sections"]:
        rows.append(f'<tr class="sec"><td colspan="5">{sec["title"]}</td></tr>')
        for i in sec["items"]:
            sub = i["qty"] * i["unit_inr"]
            qty = "—" if i["qty"] == 0 else str(i["qty"])
            unit = "—" if i["qty"] == 0 else f"₹{i['unit_inr']:,}"
            rows.append(
                f'<tr><td>{i["item"]}</td><td class="num">{qty}</td>'
                f'<td class="num">{unit}</td><td class="num"><b>₹{sub:,}</b></td>'
                f'<td>{tag.get(i["price_basis"], i["price_basis"])}</td></tr>')
    rows.append('<tr class="tot"><td>GRAND TOTAL — everything above</td>'
                '<td class="num"></td><td class="num"></td>'
                f'<td class="num">₹{bom["total_inr"]:,}</td><td></td></tr>')

    first = html.index('<tr class="sec"><td colspan="5">')
    last = html.index("</tr>", html.index('<tr class="tot">')) + len("</tr>")
    new_html = html[:first] + "\n".join(rows) + html[last:]
    # The headline in the opening paragraph carries the total too.
    new_html = re.sub(r"One unit, ₹[\d,]*\d", f"One unit, ₹{bom['total_inr']:,}", new_html)
    if new_html == html:
        return False
    GUIDE.write_text(new_html, encoding="utf-8")
    return True


def main() -> int:
    bom = load()
    changed = [name for name, did in
               (("docs/TERMINAL_MK3.md", rewrite_markdown(bom)),
                ("docs/submission/buylist_checklist_source.html", rewrite_buylist(bom)),
                ("docs/submission/build_guide_source.html", rewrite_guide(bom)))
               if did]
    print(f"BOM total ₹{bom['total_inr']:,} over "
          f"{sum(len(s['items']) for s in bom['sections'])} items")
    print("rewrote: " + (", ".join(changed) if changed else "nothing (already current)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
