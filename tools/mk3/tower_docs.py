"""Plan Urena · MK3 TOWER edition: build pack and shop sheet (HTML -> PDF with Chromium).

    python3 tools/mk3/tower_cad.py        # first: CAD, clearance, report.json
    python3 tools/mk3/tower_docs.py       # HTML (tools/mk3/tower/out/docs/) + print pack zip
    node tools/mk3/tower_pdf.mjs          # PDFs into docs/mk3/

Every number on the pages comes from tower/out/report.json or from the parameters in tower_cad.py.
Prices are estimates and say so.
"""
import html, json, os, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'tower', 'out')
DOCS = os.path.join(OUT, 'docs')
IMG = os.path.join(ROOT, 'tower', 'img')
REPO = os.path.abspath(os.path.join(ROOT, '..', '..'))
os.makedirs(DOCS, exist_ok=True)
R = json.load(open(os.path.join(OUT, 'report.json')))
P = R['parts']
GRAMS = R['total_print_grams']
BBOX = R['assembly_bbox_mm']
ZT = R['tilt_axis_height_mm']
NCHECK = len(R['clearance'])
assert R['clearance_ok'], 'clearance failed: fix the CAD before writing docs'

def rs(a, b):
    return f'₹{a:,}–{b:,}'

# ---------------------------------------------------------------- lists
HAVE = [
    ('2 × A4988 stepper drivers', 'from MK2. Test each one first (the self-test does it).'),
    ('12 V adapter', 'check the label: 3 A or more is best. A 2 A adapter works if you set the driver current low. Replace any damaged cable.'),
    ('2 × NEMA17 motors + their 4-pin cables', 'from MK2. The shaft must be 5 mm.'),
    ('USB camera (38 × 38 mm board)', 'from MK2. Measure your board: the pocket is 38.6 mm.'),
    ('Beacon + decoy', 'no change.'),
    ('Laptop with the Live page', 'no change.'),
]
# (item, qty, low, high, where, note)
BUY = [
    ('Arduino UNO R3 + USB-B cable', 1, 450, 700, 'Amar shop', 'CH340 clone is fine. Amazon: "Arduino UNO R3 CH340 with cable".'),
    ('CNC Shield V3 for UNO', 1, 250, 350, 'Amar shop', 'It must say "V3" and fit on an UNO. Amazon: "CNC shield V3 Arduino UNO".'),
    ('12 mm laser module, red 650 nm, 5 mW, 5 V', 1, 100, 200, 'Amar shop', 'Only 5 mW. Never a "burning" laser. Amazon: "650nm 5mW laser module 12mm".'),
    ('Dupont jumper wires, female-female, 20 cm', 1, 60, 100, 'Amar shop', 'One pack. For the laser.'),
    ('Fuse holder 5×20 mm + 3 A fuses + rocker switch', 1, 60, 120, 'Amar shop', 'Safety for the 12 V. Optional but cheap.'),
    ('Heatsinks for A4988 (if the drivers have none)', 1, 20, 40, 'Amar shop', 'Small stick-on type.'),
    ('M3 screw kit (6 to 30 mm) with nuts and washers', 1, 250, 400, 'Hardware shop', 'Covers every screw below. Amazon: "M3 screw nut assortment kit".'),
    ('M2 × 6 self-tapping screws', 1, 20, 40, 'Hardware shop', 'Four are used for the camera board.'),
    ('Super glue + rubber feet (or non-slip tape)', 1, 60, 120, 'Hardware shop', 'Three feet under the tripod legs.'),
]
BUY_LO = sum(q * a for _, q, a, _, _, _ in BUY)
BUY_HI = sum(q * b for _, q, _, b, _, _ in BUY)
PRINT_LO, PRINT_HI = GRAMS * 5, GRAMS * 10
COUPON_G = P['00_test_coupon']['grams_petg']
SELF_LO, SELF_HI = 240, 400

NOT_NEEDED = 'No bearings, belts or pulleys. No angle sensors, no splitter. No breadboard, no soldering. No metal shaft hubs (the hubs are printed and clamp with a set screw).'

PRINT = [  # name, title, qty, supports, orientation, note
    ('01_tripod_base', 'Tripod base', 1, 'No', 'Flat on the bed, as shown.', 'Three legs and the square pad. Four nut pockets on the underside.'),
    ('02_tower_sleeve', 'Tower sleeve', 1, 'No', 'Foot flange on the bed, open end up.', 'Holds the pan motor. A cable slot near the bottom.'),
    ('03_tower_cap', 'Tower cap', 1, 'No', 'Flat on the bed.', 'The pan motor screws to its underside.'),
    ('04_pan_hub', 'Pan hub', 1, 'No', 'Small end down, wide end up.', 'Clamps on the pan shaft. Slot for one M3 nut.'),
    ('05_tilt_mount', 'Tilt mount', 1, 'No', 'Plate down, wall and ribs standing up.', 'The tilt motor screws to its wall.'),
    ('06_head', 'Head', 1, 'Yes, only under the camera plate', 'Stand it on the rear of the clamp, laser tube pointing up.', 'Camera on the front, laser tube on top, clamps on the tilt shaft.'),
    ('00_test_coupon', 'Test coupon (print FIRST)', 1, 'No', 'Flat on the bed.', 'Checks every fit in about an hour. See page "Do the parts fit?".'),
]
SETTINGS = 'Material PETG (PLA is fine for the first test). Layer 0.2 mm. 4 walls. Infill 25%. No brim needed.'

CSS = '''
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact }
body { margin: 0; font: 10.5pt/1.45 Inter, "Helvetica Neue", Helvetica, Arial, sans-serif; color: #15171a }
.pg { width: 210mm; height: 297mm; padding: 13mm 14mm 14mm; page-break-after: always; position: relative; overflow: hidden }
.pg:last-child { page-break-after: auto }
h1 { font-size: 27pt; line-height: 1.05; margin: 0 0 4mm; letter-spacing: -.02em }
h2 { font-size: 17pt; margin: 0 0 3mm; letter-spacing: -.01em }
h3 { font-size: 11.5pt; margin: 4mm 0 1.5mm }
p { margin: 0 0 2.5mm }
.kick { font: 600 8pt/1 "SF Mono", Menlo, Consolas, monospace; letter-spacing: .14em; text-transform: uppercase; color: #0a7ea4; margin: 0 0 3mm }
.mute { color: #60666e }
.small { font-size: 8.5pt }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 4mm 0 }
.tile { border: 1px solid #d9dde2; border-radius: 3mm; padding: 3mm 3.5mm; background: #f7f8fa }
.tile b { display: block; font-size: 17pt; letter-spacing: -.02em }
.tile span { font-size: 8pt; color: #60666e }
table { border-collapse: collapse; width: 100%; font-size: 9pt }
th { text-align: left; font: 600 7.5pt/1.2 "SF Mono", Menlo, Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; color: #60666e; background: #f1f3f5; padding: 2mm 2.5mm; border-bottom: 1px solid #d9dde2 }
td { padding: 2mm 2.5mm; border-bottom: 1px solid #e6e9ed; vertical-align: top }
td.n, th.n { text-align: right; white-space: nowrap }
.box { border: 1px solid #d9dde2; border-radius: 3mm; padding: 3mm 4mm; margin: 3mm 0; background: #fff }
.warn { border-color: #e7b9b5; background: #fdf0ef }
.good { border-color: #b7dcc6; background: #eff8f2 }
.note { border-color: #efdca6; background: #fff9e6 }
.chk { display: inline-block; width: 4mm; height: 4mm; border: 1.3px solid #15171a; border-radius: 1mm; vertical-align: -0.8mm; margin-right: 2mm }
.tag { display: inline-block; font: 600 7pt/1 "SF Mono", Menlo, monospace; letter-spacing: .06em; padding: 1.2mm 2mm; border-radius: 10mm; background: #e7f1f7; color: #0a6687; text-transform: uppercase }
.tag.g { background: #e3f3ea; color: #1c7a45 } .tag.a { background: #fdf0d2; color: #8a5a00 }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm }
.img { width: 100%; border: 1px solid #e6e9ed; border-radius: 3mm; background: #fff }
.imgc { display: block; margin: 0 auto; max-width: 100%; max-height: 100% }
.step { display: grid; grid-template-columns: 9mm 1fr; gap: 3mm; margin: 0 0 3.2mm; break-inside: avoid }
.step .no { width: 9mm; height: 9mm; border-radius: 50%; background: #0a7ea4; color: #fff; font: 700 11pt/9mm sans-serif; text-align: center }
.step .chkline { font-size: 9pt; color: #1c7a45; background: #eff8f2; border-radius: 2mm; padding: 1.2mm 2.5mm; margin-top: 1.3mm }
.foot { position: absolute; left: 14mm; right: 14mm; bottom: 7mm; font-size: 7pt; color: #8e8e93; display: flex; justify-content: space-between }
.big { font-size: 13pt; font-weight: 600 }
ul { margin: 0 0 2.5mm; padding-left: 5mm } li { margin: 0 0 1mm }
.say { font-style: italic; color: #2b3138 }
'''

def page(inner, n, total, title):
    return f'<section class="pg">{inner}<div class="foot"><span>{title} · internal · Team ZeroDrift</span><span>{n} / {total}</span></div></section>'

def img(name, cls='img', style=''):
    return f'<img class="{cls}" style="{style}" src="../../img/{name}.jpg">'

def buy_rows(where=None):
    rows = ''
    for it, q, a, b, w, note in BUY:
        if where and w != where:
            continue
        rows += f'<tr><td><span class="chk"></span>{html.escape(it)}</td><td class="n">{q}</td><td class="n">{rs(a, b)}</td><td>{html.escape(w)}</td><td class="mute small">{html.escape(note)}</td></tr>'
    return rows

def print_rows():
    rows = ''
    for name, title, q, sup, ori, note in PRINT:
        i = P[name]
        bb = i['print_bbox_mm']
        rows += (f'<tr><td><b>{html.escape(title)}</b><br><span class="mute small">{name}.stl</span></td><td class="n">{q}</td>'
                 f'<td class="n">{bb[0]:.0f} × {bb[1]:.0f} × {bb[2]:.0f}</td><td class="n">{i["grams_petg"]:.0f} g</td>'
                 f'<td>{html.escape(sup)}</td><td class="small">{html.escape(ori)} {html.escape(note)}</td></tr>')
    return rows

# ---------------------------------------------------------------- shop sheet pages
def shop_pages():
    a = f'''<div class="kick">Shop slip 1 of 3 · Amar shop (electronics)</div>
<h2>Show this to the shopkeeper</h2>
<p class="say">"Hello. I am building a small camera-and-laser turntable with two stepper motors. I need these parts. Please check that each one is the exact type written."</p>
<table><tr><th>Item</th><th class="n">Qty</th><th class="n">Price (estimate)</th><th>Shop</th><th>Must be</th></tr>{buy_rows('Amar shop')}</table>
<div class="box note"><b>Check at the counter</b><ul class="small">
<li><b>CNC shield:</b> the text on the board says "V3", and it fits on the UNO (it has 4 driver sockets).</li>
<li><b>Laser:</b> 12 mm wide metal tube, red, 5 mW, 5 V. Ask for the datasheet or label.</li>
<li><b>UNO:</b> has a USB-B cable. A CH340 clone is fine.</li></ul></div>
<div class="box"><b>We already have:</b> 2 × A4988 drivers, a 12 V adapter, 2 × NEMA17 motors, a USB camera. Do not buy these again.</div>
<p class="big">Amar shop total: about {rs(sum(q*a for _, q, a, _, w, _ in BUY if w == 'Amar shop'), sum(q*b for _, q, _, b, w, _ in BUY if w == 'Amar shop'))}</p>'''
    b = f'''<div class="kick">Shop slip 2 of 3 · Hardware shop (screws and glue)</div>
<h2>Screws, nuts and small things</h2>
<p class="say">"I need M3 screws and nuts in a kit, some tiny self-tapping screws, and strong glue."</p>
<table><tr><th>Item</th><th class="n">Qty</th><th class="n">Price (estimate)</th><th>Shop</th><th>Must be</th></tr>{buy_rows('Hardware shop')}</table>
<h3>What the screw kit must contain (counts we use)</h3>
<table><tr><th>Screw</th><th class="n">How many</th><th>Used for</th></tr>
<tr><td>M3 × 8 mm</td><td class="n">11</td><td>4 pan motor · 4 tilt motor · 1 hub set screw · 1 head set screw · 1 laser clamp</td></tr>
<tr><td>M3 × 10 mm</td><td class="n">3</td><td>tilt mount onto the hub</td></tr>
<tr><td>M3 × 12 mm</td><td class="n">8</td><td>4 cap to tower · 4 tower to base</td></tr>
<tr><td>M3 nut</td><td class="n">6</td><td>4 under the base · 1 hub · 1 head</td></tr>
<tr><td>M2 × 6 mm self-tapping</td><td class="n">4</td><td>camera board</td></tr></table>
<p class="small mute">A kit of 6 to 30 mm M3 screws has all of these with spares. Buy a few extra M3 × 8.</p>
<p class="big">Hardware shop total: about {rs(sum(q*a for _, q, a, _, w, _ in BUY if w == 'Hardware shop'), sum(q*b for _, q, _, b, w, _ in BUY if w == 'Hardware shop'))}</p>
<div class="box note"><b>Amazon (only if a shop does not have it).</b> Search words: "Arduino UNO R3 CH340", "CNC shield V3 Arduino UNO", "650nm 5mW laser module 12mm", "M3 screw nut assortment kit", "Dupont jumper wire female female". Check the delivery date: we need the parts before printing ends.</div>
<div class="box good"><b>Not needed any more:</b> {NOT_NEEDED}</div>'''
    c = f'''<div class="kick">Shop slip 3 of 3 · 3D print shop</div>
<h2>Print job sheet</h2>
<p class="say">"Please print these parts in PETG. The files are attached. Print the test coupon first so we can check the fits."</p>
<table><tr><th>Part</th><th class="n">Qty</th><th class="n">Size mm</th><th class="n">Weight</th><th>Supports</th><th>How to lay it</th></tr>{print_rows()}</table>
<div class="box"><b>Settings:</b> {SETTINGS}<br><b>Files:</b> one STL per part in the pack (<span class="small">Plan_Urena_Tower_print_pack.zip</span>). STEP files are inside too, in case the shop needs them.<br>
<b>Total:</b> {GRAMS} g for the six parts (+ {COUPON_G:.0f} g for the coupon). About 14–20 hours on a normal printer (estimate). Biggest part: the tripod base, {P['01_tripod_base']['print_bbox_mm'][0]:.0f} × {P['01_tripod_base']['print_bbox_mm'][1]:.0f} mm, fits a 220 mm bed.</div>
<div class="cols"><div class="box good"><b>At a print shop</b><br>About {rs(PRINT_LO, PRINT_HI)} (₹5–10 per gram, ask for a quote) + {rs(round(COUPON_G*5), round(COUPON_G*10))} for the coupon.</div>
<div class="box"><b>On a friend's printer</b><br>About {rs(SELF_LO, SELF_HI)} of PETG for the six parts (estimate).</div></div>
<div class="cols">{img('p01', 'img', 'height:40mm;object-fit:contain')}{img('p06', 'img', 'height:40mm;object-fit:contain')}</div>
<p class="small mute">Left: tripod base. Right: head (camera plate on the front, laser tube on top).</p>'''
    return [a, b, c]

# ---------------------------------------------------------------- build pack pages
def pack_pages():
    pages = []
    pages.append(f'''<div class="kick">Plan Urena · MK3 · Tower edition</div>
<h1>Two big stepper motors.<br>One tripod. Nothing to solder.</h1>
<p class="mute">The direct-drive pan-tilt tower, built from the design you chose: the pan motor stands inside a printed tower, the tilt motor lies on top of it, and the camera and laser clamp straight onto the tilt shaft. A CNC shield plugs into an Arduino UNO, so there is no breadboard.</p>
<div style="height:108mm;display:flex;align-items:center;justify-content:center">{img('hero', 'imgc', 'border:0;max-height:108mm')}</div>
<div class="tiles">
<div class="tile"><b>0.11°</b><span>smallest move per motor step (1/16 step)</span></div>
<div class="tile"><b>{GRAMS} g</b><span>to print, six parts, PETG</span></div>
<div class="tile"><b>{NCHECK - 0}</b><span>clearance checks, {sum(len(v) for v in R["clearance"].values())} collisions (pan ±90°, tilt ±45°)</span></div>
<div class="tile"><b>{rs(BUY_LO + PRINT_LO, BUY_HI + PRINT_HI)}</b><span>all in, parts + print shop (estimate)</span></div></div>
<div class="box note"><b>Honest status.</b> This design is checked on the computer only. It is not printed or tested yet. Print the test coupon first, then the parts. Prices are estimates: confirm them at the shop.</div>''')

    pages.append(f'''<div class="kick">1 · What we have, what we buy</div>
<h2>We already own most of it</h2>
<div class="cols"><div><h3>Already have ✓</h3><table>{''.join(f'<tr><td><b>{html.escape(a)}</b><br><span class="mute small">{html.escape(b)}</span></td></tr>' for a, b in HAVE)}</table></div>
<div><h3>Not needed in this design</h3><div class="box good small">{NOT_NEEDED}</div>
<h3>Why it is cheaper than the belt design</h3><p class="small">The belt design needs 4 bearings, 3 pulleys, 4 belts and 1,074 g of printing. The tower needs none of those parts and prints {GRAMS} g.</p></div></div>
<h3>Buy list</h3>
<table><tr><th>Item</th><th class="n">Qty</th><th class="n">Price (estimate)</th><th>Where</th><th>Note</th></tr>{buy_rows()}</table>
<p class="small mute">If a motor or driver from MK2 turns out to be damaged: NEMA17 about ₹400–600 each, A4988 about ₹150–200 each. The shop slips for carrying are in a separate short PDF.</p>''')

    pages.append(f'''<div class="kick">2 · Shop slips</div>
<h2>Go shopping: Amar shop first, Amazon as backup</h2>
<p>Take the separate <b>shop sheet</b> (3 pages) with you. It has one slip for each place. Quick version:</p>
<table><tr><th>Where</th><th>What to get</th><th class="n">About</th></tr>
<tr><td><b>Amar shop</b><br><span class="mute small">electronics</span></td><td>UNO R3 + cable · CNC shield V3 · 12 mm laser module · jumper wires · fuse holder + fuses + switch · heatsinks</td><td class="n">{rs(sum(q*a for _, q, a, _, w, _ in BUY if w == 'Amar shop'), sum(q*b for _, q, _, b, w, _ in BUY if w == 'Amar shop'))}</td></tr>
<tr><td><b>Hardware shop</b></td><td>M3 screw kit with nuts · M2 × 6 self-tapping · super glue · rubber feet</td><td class="n">{rs(sum(q*a for _, q, a, _, w, _ in BUY if w == 'Hardware shop'), sum(q*b for _, q, _, b, w, _ in BUY if w == 'Hardware shop'))}</td></tr>
<tr><td><b>3D print shop</b></td><td>The six parts (+ the coupon first), PETG, {GRAMS} g</td><td class="n">{rs(PRINT_LO, PRINT_HI)}</td></tr>
<tr><td><b>Amazon</b><br><span class="mute small">only if needed</span></td><td>Anything the shops do not have. Search words are on shop slip 2.</td><td class="n">same</td></tr></table>
<h3>Budget</h3>
<table><tr><th>Part of the project</th><th class="n">Cost (estimate)</th></tr>
<tr><td>Parts to buy (list above)</td><td class="n">{rs(BUY_LO, BUY_HI)}</td></tr>
<tr><td>Printing {GRAMS} g at a print shop (₹5–10 per gram)</td><td class="n">{rs(PRINT_LO, PRINT_HI)}</td></tr>
<tr><td>Test coupon ({COUPON_G:.0f} g), print first</td><td class="n">{rs(round(COUPON_G*5), round(COUPON_G*10))}</td></tr>
<tr><td><b>Total with a print shop</b></td><td class="n"><b>{rs(BUY_LO + PRINT_LO + round(COUPON_G*5), BUY_HI + PRINT_HI + round(COUPON_G*10))}</b></td></tr>
<tr><td><b>Total if a friend prints it</b> (PETG only)</td><td class="n"><b>{rs(BUY_LO + SELF_LO, BUY_HI + SELF_HI)}</b></td></tr></table>
<h3>The order that saves time</h3>
<ol><li><b>Today:</b> send the coupon STL to the print shop. It is small and quick.</li><li><b>Same day:</b> buy the electronics and the screw kit.</li><li><b>When the coupon fits:</b> print the six parts. The parts take about 14–20 hours.</li><li>Wire the UNO and CNC shield while the printer runs, and test each motor on the bench.</li></ol>
<div class="box warn"><b>Safety.</b> The laser is 5 mW, red. Never look into the beam and never point it at a person or at a shiny surface. The 12 V adapter needs an undamaged cable and a fuse. Never plug or unplug a motor or a driver with 12 V on.</div>''')

    pages.append(f'''<div class="kick">3 · Print job sheet</div>
<h2>What to print, and how</h2>
<table><tr><th>Part</th><th class="n">Qty</th><th class="n">Size mm</th><th class="n">Weight</th><th>Supports</th><th>How to lay it</th></tr>{print_rows()}</table>
<div class="box"><b>Settings:</b> {SETTINGS}<br><b>Total:</b> {GRAMS} g for the six parts. Weights are estimates at 25% infill.</div>
<div class="cols">{img('p02', 'img', 'height:52mm;object-fit:contain')}{img('p05', 'img', 'height:52mm;object-fit:contain')}</div>
<p class="small mute">Left: tower sleeve. Right: tilt mount. The other parts are pictured on the shop sheet and in the exploded view.</p>
<div class="box note"><b>Why the head needs supports.</b> The camera plate is wider than the arm behind it. Use tree supports and only under that plate. Do not support the bores; drill them out with a 5 mm and a 12 mm drill if they come out tight.</div>''')

    cl = R['clearance']
    pages.append(f'''<div class="kick">4 · Do the parts fit?</div>
<h2>Every bought part against its printed hole</h2>
<table><tr><th>Bought part</th><th class="n">Its size</th><th>Our hole or pocket</th><th class="n">Gap</th></tr>
<tr><td>NEMA17 motor body (pan)</td><td class="n">42.3 mm square</td><td>Tower cavity 44.6 mm square</td><td class="n">1.15 mm each side</td></tr>
<tr><td>NEMA17 pilot boss (pan and tilt)</td><td class="n">22 mm</td><td>Hole in the cap and in the wall: 22.3 mm</td><td class="n">0.15 mm each side</td></tr>
<tr><td>NEMA17 screw holes</td><td class="n">31 mm square</td><td>4 clearance holes, 3.2 mm</td><td class="n">M3 passes</td></tr>
<tr><td>Motor shaft (pan and tilt)</td><td class="n">5 mm</td><td>Bore in the hub and in the head: 5.2 mm</td><td class="n">0.1 mm each side</td></tr>
<tr><td>M3 nut (across flats 5.5)</td><td class="n">2.4 mm thick</td><td>Slot 5.9 × 2.6 mm</td><td class="n">drops in</td></tr>
<tr><td>M3 screw cutting its own thread</td><td class="n">3 mm</td><td>Pilot hole 2.7 mm</td><td class="n">bites</td></tr>
<tr><td>USB camera board</td><td class="n">38 mm square</td><td>Pocket 38.6 mm square, 2.4 mm deep</td><td class="n">0.3 mm each side</td></tr>
<tr><td>Laser module</td><td class="n">12 mm</td><td>Bore 12.3 mm + one M3 clamp screw</td><td class="n">push fit</td></tr>
<tr><td>Tower flange to tripod base</td><td class="n">4 × M3 at 66 mm square</td><td>4 holes + 4 nut pockets underneath</td><td class="n">bolts</td></tr></table>
<h3>Moving clearance (computer check of the real 3D shapes)</h3>
<table><tr><th>Check</th><th class="n">Poses</th><th class="n">Collisions</th></tr>
<tr><td>Standing still, every part against every part</td><td class="n">1</td><td class="n">{len(cl["static @pan0 tilt0"])}</td></tr>
<tr><td>Head and plate turning against the tower and base: pan −90° to +90°</td><td class="n">6</td><td class="n">{sum(len(v) for k, v in cl.items() if k.startswith("fixed-vs-pan"))}</td></tr>
<tr><td>Head against the tilt mount and plate: tilt −45° to +45°</td><td class="n">6</td><td class="n">{sum(len(v) for k, v in cl.items() if k.startswith("pan-vs-tilt"))}</td></tr>
<tr><td>Head against the tower and base: tilt −45° to +45°</td><td class="n">6</td><td class="n">{sum(len(v) for k, v in cl.items() if k.startswith("fixed-vs-tilt"))}</td></tr></table>
<div class="cols" style="margin-top:3mm">{img('side_m30')}{img('side_p30')}</div>
<p class="small mute">Tilt −30° (left) and +30° (right). The head always stays about 2 mm away from the tilt wall, and the firmware stops at ±30°.</p>''')

    pages.append(f'''<div class="kick">5 · Parts and screws</div>
<h2>Exploded view</h2>
<div style="height:118mm;display:flex;align-items:center;justify-content:center">{img('expl', 'imgc', 'border:0;max-height:118mm')}</div>
<table><tr><th>No.</th><th>Part</th><th>Holds</th></tr>
<tr><td>01</td><td>Tripod base</td><td>Everything. Three legs, one pointing to the head side.</td></tr>
<tr><td>02</td><td>Tower sleeve</td><td>The pan motor hangs inside it.</td></tr>
<tr><td>03</td><td>Tower cap</td><td>The pan motor is screwed to its underside.</td></tr>
<tr><td>04</td><td>Pan hub</td><td>Clamps on the pan shaft and carries the tilt mount.</td></tr>
<tr><td>05</td><td>Tilt mount</td><td>The tilt motor is screwed to its wall, lying on its side.</td></tr>
<tr><td>06</td><td>Head</td><td>Clamps on the tilt shaft. Camera in front, laser on top.</td></tr></table>
<p class="small mute">Size when built: {BBOX[0]:.0f} × {BBOX[1]:.0f} mm footprint, {BBOX[2]:.0f} mm tall. The tilt axis is {ZT:.0f} mm above the table. The pan axis passes through the centre of the tilt motor, so the tower stays balanced.</p>''')

    steps = [
        ('Print and check the coupon', 'Print the test coupon. A NEMA17 shaft must slide into the 5.2 mm hole, an M3 screw must bite in the small hole, an M3 nut must drop into the slot, the motor pilot must sit in the 22 mm hole, the camera board must lie in the pocket and the laser must push into the round hole.', 'All six fits are right. If one is not, tell us which, and we change that one number.'),
        ('Print the six parts', f'Use the print job sheet. {GRAMS} g in total.', 'Every part is flat where it should be and the holes are clean.'),
        ('Pan motor onto the cap', 'Put the motor flange against the underside of the cap. The shaft goes up through the round hole. Fit 4 × M3 × 8 from the top.', 'The shaft sticks out about 20 mm above the cap.'),
        ('Cap and motor onto the sleeve', 'Feed the motor cable out through the slot. Lower the motor into the sleeve. Fit 4 × M3 × 12 into the four corners (they cut their own thread; do not over-tighten).', 'The cap lies flat, with no gap.'),
        ('Sleeve onto the base', 'Push 4 nuts into the pockets under the base. Stand the sleeve on the pad. Fit 4 × M3 × 12 from the top.', 'The tower stands straight. The cable slot faces away from the head side.'),
        ('Pan hub', 'Drop a nut into the hub slot. Slide the hub onto the shaft, wide end up. Turn it so the set screw meets the flat side of the shaft. Tighten 1 × M3 × 8. Leave 1 mm above the cap.', 'Turn the hub by hand: the shaft turns with it. It does not rub the cap.'),
        ('Tilt mount on the hub', 'Put 3 × M3 × 10 into the plate (the heads sit in the round pockets on top). Screw them down into the hub. The shaft tip goes into the small pocket under the plate.', 'The plate is level and turns with the shaft.'),
        ('Tilt motor', 'Slide the motor in from the back, flat on the plate, its round boss into the hole in the wall. Fit 4 × M3 × 8 from the front of the wall. The cable points backwards.', 'The shaft sticks out about 20 mm beyond the wall.'),
        ('Head, camera and laser', 'Drop a nut into the head slot. Slide the head on the tilt shaft until it is 1–2 mm from the wall. Tighten 1 × M3 × 8 on the flat. Mark and pre-drill the camera board corners, then fix it with 4 × M2 × 6 (or a little glue). Push in the laser and tighten the top clamp screw.', 'With the power off, the head swings by hand about ±45° without touching anything.'),
        ('Wire it, flash it, test it', 'Follow the next two pages: plug-in wiring, then the firmware and the tests.', 'The Live page says the rig is connected.'),
    ]
    half = 5
    for k in range(2):
        body = ''
        for i, (t, d, c) in enumerate(steps[k * half:(k + 1) * half], start=k * half + 1):
            body += f'<div class="step"><div class="no">{i}</div><div><b>{html.escape(t)}.</b> {html.escape(d)}<div class="chkline">CHECK: {html.escape(c)}</div></div></div>'
        extra = f'<div style="height:62mm;display:flex;align-items:center;justify-content:center;margin-top:2mm">{img("in1" if k == 0 else "head", "imgc", "border:0;max-height:62mm")}</div><p class="small mute">{"Inside view: the pan motor hangs from the cap, the tower sleeve is hidden." if k == 0 else "Head, camera and laser, close up."}</p>'
        pages.append(f'<div class="kick">6 · Build steps {k * half + 1}–{(k + 1) * half}</div><h2>{"Mechanics" if k == 0 else "Top half and finishing"}</h2>{body}{extra}')

    pages.append(f'''<div class="kick">7 · Wiring and firmware</div>
<h2>Plug it in</h2>
<div style="height:108mm;display:flex;align-items:center;justify-content:center">{img('plug_in', 'imgc', 'max-height:108mm')}</div>
<h3>Put the firmware on the UNO</h3>
<ol class="small"><li>Plug the UNO into the laptop with the USB cable. Power off the 12 V.</li>
<li>Run <b>tools/rig/flash.sh tower</b>. It builds the direct-drive version (ratio 1:1, pan ±90°, tilt ±30°, gentle speed).</li>
<li>The board prints <b>"# ZeroDrift Mk2 ready, encoders=no, belts=1:1"</b>. That line means it worked.</li></ol>
<h3>Set the Live page</h3>
<ol class="small"><li>Rig type: <b>MK2 · steppers</b>. Drive: <b>Direct drive (1:1)</b>.</li>
<li>Press <b>CONNECT RIG</b>, then <b>START CAMERA</b>. Turn on the 12 V.</li>
<li>Press <b>TEST MOTION</b>: pan and tilt must move the way the picture on screen moves. If one goes the wrong way, flip the motor plug, or use INVERT.</li>
<li>Switch on the laser and press <b>SET AIM</b> on the laser dot.</li></ol>
<div class="box note small"><b>Driver current.</b> Fit all 3 jumpers under each A4988 (1/16 step). Turn the small screw on each driver until the motor is strong enough not to skip steps. Keep the driver only warm. If a motor is too hot to touch, turn it down.</div>''')

    pages.append(f'''<div class="kick">8 · Tests and fixes</div>
<h2>Is it working?</h2>
<p class="small mute">These are our targets. We have not measured them yet. Write the real result next to each one.</p>
<table><tr><th></th><th>Test</th><th>Target</th><th>Result</th></tr>
<tr><td><span class="chk"></span></td><td>Pan and tilt directions on TEST MOTION</td><td>Both right</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>Laser dot after SET AIM, beacon 2 m away</td><td>Dot on the beacon</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>Time to lock on the blinking beacon</td><td>About 2 s or less</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>Decoy next to the beacon, 10 tries</td><td>0 wrong locks</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>Cover the beacon, then uncover it</td><td>Holds, then locks again</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>Move the beacon left, right, up, down</td><td>The dot follows</td><td></td></tr>
<tr><td><span class="chk"></span></td><td>10 minutes running, then press C (centre)</td><td>Back to the same spot</td><td></td></tr></table>
<h3>If something goes wrong</h3>
<table><tr><th>What you see</th><th>What to do</th></tr>
<tr><td>A motor buzzes and does not turn</td><td>Check the 4-pin plug sits fully in. Check the 12 V is on. Turn the driver current up a little.</td></tr>
<tr><td>A motor turns the wrong way</td><td>Flip that motor's plug, or use INVERT on the Live page.</td></tr>
<tr><td>A hub or the head slips on its shaft</td><td>The set screw must press on the flat side. Tighten it. Add a drop of thread-lock.</td></tr>
<tr><td>The head drops or shakes</td><td>The camera and laser are too heavy or off-centre. Keep the head under about 150 g.</td></tr>
<tr><td>It loses position (centre is not centre)</td><td>Turn the driver current up a little or lower the speed. Check the jumpers (1/16).</td></tr>
<tr><td>A driver gets too hot</td><td>Fit the heatsink, turn the current down, add a small fan.</td></tr></table>
<h3>If you need finer aim later</h3>
<p class="small">One step is 0.11°, about 2 pixels on the MK2 camera. For 0.056°, use DRV8825 drivers at 1/32 (set MICROSTEPS to 32 in the firmware). For 0.028° use the belt design, Plan Urena. The UNO, shield, motors and firmware carry over.</p>''')
    return pages

def doc(title, pages):
    total = len(pages)
    body = ''.join(page(p, i + 1, total, title) for i, p in enumerate(pages))
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title><style>{CSS}</style><body>{body}</body></html>'

pack = pack_pages()
shop = shop_pages()
open(os.path.join(DOCS, 'pack.html'), 'w').write(doc('Plan Urena · MK3 Tower build pack', pack))
open(os.path.join(DOCS, 'shop.html'), 'w').write(doc('Plan Urena · MK3 Tower shop sheet', shop))

README = f'''Plan Urena MK3 TOWER print pack (Team ZeroDrift)

Six parts + a test coupon. PETG, 0.2 mm layers, 4 walls, 25% infill.
Print 00_test_coupon first (about an hour). If every fit is right, print the rest.

  01_tripod_base   x1   flat
  02_tower_sleeve  x1   foot flange on the bed
  03_tower_cap     x1   flat
  04_pan_hub       x1   small end down
  05_tilt_mount    x1   plate down
  06_head          x1   stand on the clamp rear, laser tube up; supports only under the camera plate

STL = print files (each already lying in its print orientation). STEP = the same parts for editing.
Total {GRAMS} g for the six parts. Sizes in mm. Clearance checked for pan +/-90 and tilt +/-45.
'''
def pack_zip():
    z = os.path.join(REPO, 'docs', 'mk3', 'Plan_Urena_Tower_print_pack.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('PlanUrena_Tower_print/README.txt', README)
        for n in sorted(P):
            if not P[n]['printed']:
                continue
            zf.write(os.path.join(OUT, 'print', n + '.stl'), f'PlanUrena_Tower_print/stl/{n}.stl')
            sp = os.path.join(OUT, 'step', n + '.step')
            if os.path.exists(sp):
                zf.write(sp, f'PlanUrena_Tower_print/step/{n}.step')
    return z

if __name__ == '__main__':
    z = pack_zip()
    print(f'pages written: pack {len(pack)}, shop {len(shop)}; buy {rs(BUY_LO, BUY_HI)}, print {rs(PRINT_LO, PRINT_HI)}, {GRAMS} g; zip {os.path.getsize(z) // 1024} KB')
