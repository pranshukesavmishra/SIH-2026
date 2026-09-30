"""Plan Urena: build the hidden build page, the Plan PDF, the print-shop PDF and the print pack.

    python3 tools/mk3/mk3_cad.py        # first: parts, report.json
    python3 tools/mk3/urena_docs.py     # then: docs/mk3.html, docs/mk3/*.html, the zip
    node tools/mk3/urena_pdf.mjs        # last: prints the two PDFs with Chromium

Everything here is internal. The name "Plan Urena" and "MK3" must never appear on a public page.
"""
import html, json, os, shutil, zipfile
from urena_data import (PRINT, print_rows, total_grams, BUY, buy_totals, print_cost, PRINT_COST_PER_G, REUSE,
                        CAMERAS, PINS, SCREWS, BELTS, P, REPORT)
import urena_svg as SV

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..'))
DOCS = os.path.join(REPO, 'docs')
MK3 = os.path.join(DOCS, 'mk3')
E = html.escape


def rs(n):
    return '₹' + f'{int(round(n)):,}'


def g_(v):
    return '<1 g' if v < 1 else f'{v:.0f} g'


def rng(lo, hi):
    return f'{rs(lo)}–{int(round(hi)):,}' if lo != hi else rs(lo)


BUY_LO, BUY_HI = buy_totals()
PR_LO, PR_HI = print_cost()
GRAMS = total_grams()
FITS_P, FITS_T = BELTS['pan']['belts_that_fit_mm'], BELTS['tilt']['belts_that_fit_mm']
SPD = BELTS['steps_per_output_deg']


# ================================================================== sections (shared by the page and the PDF)
def sec_overview(img):
    facts = [('Drive', '4:1 GT2 belts', 'on both axes'), ('Fine steps', f'{SPD:.1f}', 'motor steps per degree'),
             ('Travel', 'pan ±150° · tilt ±40°', 'clear to −45 / +60 in CAD'), ('Bearings', '2 × 6808 + 2 × 6806', 'hollow: cables go through'),
             ('Printed', f'20 files · ≈{GRAMS:,} g', 'PETG'), ('Controller', 'UNO + CNC Shield V3', 'no breadboard, fused 12 V'),
             ('To buy', rng(BUY_LO, BUY_HI), 'incl. spares'), ('Printing', rng(PR_LO, PR_HI), f'at ₹{PRINT_COST_PER_G[0]}–{PRINT_COST_PER_G[1]} per gram')]
    cards = ''.join(f'<div class="fact"><span>{a}</span><b>{b}</b><em>{c}</em></div>' for a, b, c in facts)
    rows = [('Frame', 'Acrylic, L-brackets, couplings', '3D-printed PETG, designed to fit'),
            ('Drive', 'Motor shafts carry the load', '4:1 belts on both axes: 4 × torque, 4 × finer'),
            ('Bearings', 'None of their own', 'Big hollow bearings: stiff, no wobble'),
            ('Tilt motor', 'On the moving head frame', 'On the deck, under the head: compact and balanced'),
            ('Cables', 'Loose loop around the rig', 'Down the hollow middle'),
            ('Wiring', 'Breadboard + loose jumpers', 'UNO + CNC shield: everything plugs in'),
            ('12 V power', 'Adapter pigtail into a breadboard', 'Panel jack → 3 A fuse → switch → screw terminal'),
            ('Pan sensor', 'On the output', 'On the pan motor shaft: 4 × finer reading')]
    trows = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    steps = [('Buy', 'One trip to Amar Robotics and a bearing shop, plus one online order for belts.'),
             ('Print the coupon', 'One small print. Check the fits (page "Tests").'),
             ('Print everything', f'≈{GRAMS:,} g, about 60–80 printer-hours at normal speed.'),
             ('Assemble', '14 steps, about one day.'), ('Wire + flash', 'Half a day. Nothing to solder.'),
             ('Test + tune', 'Self-test, belt tension, laser aim, then the Live page.')]
    tl = ''.join(f'<li><b>{i + 1}. {a}</b><span>{b}</span></li>' for i, (a, b) in enumerate(steps))
    return f'''
<div class="hero"><img src="{img}asm_iso.jpg" alt="Plan Urena pan-tilt, assembled"></div>
<p class="lead">A stiff, belt-driven pan-tilt for the tracker, printed in PETG and built around big hollow bearings.
It uses the same software and the same protocol as MK2. The motors, drivers, sensors and camera come from MK2.</p>
<div class="facts">{cards}</div>
<h3>What changes from MK2</h3>
<div class="tw"><table><tr><th></th><th>MK2</th><th>Plan Urena</th></tr>{trows}</table></div>
<h3>Three ways to build a pan-tilt, and why we chose belts</h3>
<div class="tw"><table><tr><th></th><th>Printed gears</th><th>Direct drive (motor = axis)</th><th>Belts 4:1 + bearings (Plan Urena)</th></tr>
<tr><td><b>Seen in</b></td><td>Hobby webcam trackers with big printed spur gears</td><td>Our MK1 / MK2</td><td>Compact belt pan-tilts with a tripod base and the tilt motor on the turntable</td></tr>
<tr><td><b>Accuracy</b></td><td>Printed teeth have 0.3–1° of play (backlash): the aim wobbles when it reverses</td><td>Limited by the motor step and any load on its shaft</td><td><b>No play:</b> a tensioned GT2 belt has no backlash, and 4:1 makes each step 4× finer</td></tr>
<tr><td><b>Stability</b></td><td>Good if the frame is stiff</td><td>The motor shaft carries the whole load</td><td><b>Best:</b> big hollow bearings carry the load, the motors only turn</td></tr>
<tr><td><b>Parts to buy</b></td><td>Fewest (no belts, no pulleys)</td><td>Fewest</td><td>+ 4 bearings, 2 belts, 2 metal pulleys (≈₹1,000)</td></tr>
<tr><td><b>Easy to build</b></td><td>Easy, but gear teeth must print cleanly</td><td>Easiest</td><td>Easy: slide the motor to tighten each belt, no fine gear meshing</td></tr></table></div>
<p class="m">We keep belts: the same layout as the compact belt pan-tilt we liked (tripod base, pan motor in the base, tilt motor standing on the turntable, belt up the side), which gives the most accuracy for the least effort.</p>
<h3>The plan in six steps</h3>
<ol class="tl">{tl}</ol>
<div class="warn"><b>Keep it internal.</b> "Plan Urena" and "MK3" stay on these build pages and PDFs only.
Not on the public website, the deck, the video or any official material.</div>'''


def sec_views(img):
    shots = [('asm_exploded', 'Exploded: how the parts stack'), ('asm_front', 'Front'), ('asm_head', 'Head and tilt drive'),
             ('asm_base', 'Base, pan belt and pan motor'), ('asm_side', 'Side'), ('asm_desk', 'With the electronics box')]
    return '<div class="grid2">' + ''.join(f'<figure><img src="{img}{n}.jpg" alt="{E(c)}"><figcaption>{E(c)}</figcaption></figure>' for n, c in shots) + '</div>'


def sec_print(img, pdf=False):
    rows = print_rows()
    cards = ''
    for r in rows:
        qty = 3 if r['name'] == '02_leg_1' else r['qty']
        fname = '02_leg_1 / _2 / _3' if r['name'] == '02_leg_1' else r['name']
        bb = ' × '.join(f'{v:.0f}' for v in r['bbox'])
        cards += f'''<div class="pc"><img src="{img}parts/{r['img']}.jpg" alt="{E(r['title'])}">
<div><b>{E(r['title'])}</b><code>{fname}.stl</code><p>{E(r['what'])}</p>
<dl><dt>Qty</dt><dd>{qty}</dd><dt>Size</dt><dd>{bb} mm</dd><dt>PETG</dt><dd>≈{g_(r['grams'] * (qty if r['name'] == '02_leg_1' else 1))}</dd>
<dt>Colour</dt><dd>{r['colour']}</dd><dt>Supports</dt><dd>{r['supports']}</dd></dl>{f'<p class="note">{E(r["note"])}</p>' if r['note'] else ''}</div></div>'''
    return f'''
<p class="lead">Give the print shop the files exactly as they are: every STL is already turned the right way up on the bed.
Print the <b>test coupon first</b>, check it, then print the rest.</p>
<figure class="w">{SV.pendrive()}<figcaption>What to hand over. The STL files are what they print. The STEP files are only for editing.</figcaption></figure>
<h3>Printer settings (the same for every part)</h3>
<div class="tw"><table>
<tr><td><b>Material</b></td><td>PETG (not PLA: PLA slowly bends under the belt pull and near the motors). Head, front plate and laser holder in black; the rest any colour.</td></tr>
<tr><td><b>Layer height</b></td><td>0.2 mm, 0.4 mm nozzle</td></tr>
<tr><td><b>Walls</b></td><td>4 walls, 5 top and 5 bottom layers</td></tr>
<tr><td><b>Infill</b></td><td>40 % gyroid</td></tr>
<tr><td><b>Supports</b></td><td>None, except inside the motor pocket of the base hub</td></tr>
<tr><td><b>Brim</b></td><td>On the base hub and the electronics box</td></tr>
<tr><td><b>Scale</b></td><td>100 %. Do not rescale anything.</td></tr>
<tr><td><b>Total</b></td><td>≈{GRAMS:,} g PETG, about 60–80 printer-hours at normal speed (a fast printer takes about half). Cost at ₹{PRINT_COST_PER_G[0]}–{PRINT_COST_PER_G[1]} per gram: {rng(PR_LO, PR_HI)}. Ask for one price for the whole job.</td></tr>
</table></div>
<h3>The {len(rows) + 2} pieces</h3>
<div class="pcs">{cards}</div>'''


def sec_buy():
    out = ''
    for g, sub, items in BUY:
        lo = sum(q * p[0] for _, q, p, _, _ in items)
        hi = sum(q * p[1] for _, q, p, _, _ in items)
        rows = ''.join(f'<tr><td><b>{E(n)}</b>{f"<br><span class=m>{E(alt)}</span>" if alt else ""}</td><td class="c">{q}</td>'
                       f'<td class="r">{rng(p[0], p[1])}</td><td class="r">{rng(q * p[0], q * p[1])}</td><td><span class="where">{E(w)}</span></td></tr>'
                       for n, q, p, w, alt in items)
        out += f'''<h3>{E(g)} <span class="sub">{rng(lo, hi)}</span></h3>{f'<p class="m">{E(sub)}</p>' if sub else ''}
<div class="tw"><table><tr><th>Item</th><th>Qty</th><th>Each</th><th>Total</th><th>Where</th></tr>{rows}</table></div>'''
    return f'''
<p class="lead">Prices are estimates. Show this list at the shop and compare. <b>Spares are included</b>
(a second UNO, CNC shield, drivers, belts, a pulley and a laser) so a dead part never costs a day.</p>
<div class="facts">
<div class="fact"><span>Parts to buy</span><b>{rng(BUY_LO, BUY_HI)}</b><em>with spares</em></div>
<div class="fact"><span>Printing</span><b>{rng(PR_LO, PR_HI)}</b><em>≈{GRAMS:,} g PETG</em></div>
<div class="fact"><span>Total</span><b>{rng(BUY_LO + PR_LO, BUY_HI + PR_HI)}</b><em>MK2 parts reused</em></div>
<div class="fact"><span>Optional camera</span><b>₹2,100–4,100</b><em>see "Camera"</em></div></div>
<div class="info"><b>Where.</b> <b>Amar Robotics</b> for electronics, pulleys and the laser. A <b>bearing shop</b> for the four bearings:
say "6808 2RS, two" and "6806 2RS, two". A <b>hardware shop</b> for screws. <b>Online</b> (Robu, Amazon) for the closed belts,
which local shops rarely stock. If a shop has no 232 mm belt, a 240 mm belt fits too (anything {FITS_P[0]}–{FITS_P[-1]} mm).</div>
{out}
<div class="warn"><b>Do not buy:</b> a breadboard, a 12 V 1 A adapter, a "CNC Shield V4" (the Nano one has known design faults), or any laser stronger than 5 mW.</div>'''


def sec_reuse():
    rows = ''.join(f'<tr><td><b>{E(a)}</b></td><td><span class="tag {"ok" if b == "Yes" else ("no" if b == "No" else "mid")}">{E(b)}</span></td><td>{E(c)}</td></tr>' for a, b, c in REUSE)
    return f'''<p class="lead">Most of the electronics come straight from MK2. The frame is new.</p>
<div class="tw"><table><tr><th>MK2 part</th><th>Reuse?</th><th>Notes</th></tr>{rows}</table></div>'''


def sec_camera():
    rows = ''
    for name, price, fov_s, fov, px, why, kind in CAMERAS:
        tag = {'best': '<span class="tag ok">Best upgrade</span>', 'ok': '', 'no': '<span class="tag no">Skip</span>'}[kind]
        rows += f'<tr><td><b>{E(name)}</b> {tag}</td><td>{E(price)}</td><td>{E(fov_s)}{f"<br><b>{fov / px:.3f}°</b> per pixel" if px else ""}</td><td>{E(why)}</td></tr>'
    return f'''<p class="lead">Accuracy comes from the mechanics and from degrees per pixel, not from a fancy camera.
The belts and bearings already give the big gain. A narrower lens is the next cheap step.</p>
<div class="two"><figure class="w">{SV.camera_fov()}</figure>
<div><div class="ok"><b>Recommendation.</b> Build with the MK2 camera first. When the rig works, add the 1080p M12 board with a 6 mm lens:
about 2× finer aim for ≈₹2,100–4,100. It bolts to the front plate as it is (the slots take 28–34 mm hole patterns).</div>
<div class="info"><b>Narrow lens trade-off.</b> A 6 mm lens sees about 51° instead of 70°, so the beacon has to be closer to the centre
before the tracker can find it. The scan mode on the Live page covers that. Avoid 8 mm or longer lenses for the demo.</div></div></div>
<div class="tw"><table><tr><th>Camera</th><th>Price</th><th>View</th><th>Why</th></tr>{rows}</table></div>'''


def sec_wiring(img):
    prow = ''.join(f'<tr><td><code>{E(a)}</code></td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in PINS)
    return f'''
<figure class="w"><img src="{img}easy_wiring.png" alt="Easy wiring: UNO + CNC Shield V3"><figcaption>No breadboard, no soldering. Every wire plugs in or screws in.</figcaption></figure>
<h3>Why the old setup burned, and what stops it now</h3>
<div class="tw"><table><tr><th>What went wrong</th><th>Plan Urena</th></tr>
<tr><td>Motor current (up to 1.5 A) through breadboard strips, which are made for about 0.5 A. They get hot and arc.</td><td>12 V goes on 18 AWG silicone wire into a screw terminal on the CNC shield.</td></tr>
<tr><td>No big capacitor at the driver. Plugging in 12 V makes a voltage spike that can kill an A4988.</td><td>The CNC shield has the 100 µF capacitor built in, right beside the drivers.</td></tr>
<tr><td>A loose adapter pigtail can short.</td><td>Panel jack in the box wall, then a 3 A fuse, then a switch. A short blows a ₹5 fuse, not the drivers.</td></tr>
<tr><td>A driver running hot for a long time.</td><td>Heatsinks, a 40 mm fan in the lid, and the current set correctly (Vref below).</td></tr></table></div>
<h3>Pins (UNO + CNC Shield V3)</h3>
<div class="tw"><table><tr><th>UNO</th><th>Shield label</th><th>Goes to</th></tr>{prow}</table></div>
<p class="m">Clone shields sometimes label the SDA/SCL pins differently. Take a photo of yours and check before you plug the sensor wires in.</p>
<h3>Set the motor current (Vref) once, before the motors move</h3>
<ol class="steps">
<li>Motors plugged in, 12 V ON, USB unplugged. Multimeter on DC volts.</li>
<li>Black probe on any GND. Red probe touching the small metal screw (potentiometer) on the driver.</li>
<li>Turn the screw with a small plastic or ceramic screwdriver until the meter shows the value below. Do both drivers.</li></ol>
<div class="tw"><table><tr><th>Tiny resistor near the chip says</th><th>Set Vref to</th><th>Motor current</th></tr>
<tr><td><code>R100</code> (most boards)</td><td><b>0.64 V</b></td><td>0.8 A: runs cool, and the 4:1 belt gives plenty of torque</td></tr>
<tr><td><code>R050</code></td><td><b>0.32 V</b></td><td>0.8 A</td></tr>
<tr><td><code>R200</code></td><td><b>1.28 V</b></td><td>0.8 A</td></tr></table></div>
<p class="m">Formula: Vref = 8 × R × I. If a motor misses steps under load, raise it by 0.1 V at a time, up to 1.0 A.</p>
<h3>Five rules</h3>
<ol class="steps">
<li>Check + and − of the adapter with a multimeter before you connect it the first time.</li>
<li>Driver the right way round: its EN pin goes to the EN mark on the shield. Backwards = dead driver.</li>
<li>Never plug or unplug a motor while 12 V is on.</li>
<li>USB into the laptop first, then switch 12 V on. Switch 12 V off before unplugging USB.</li>
<li>Three jumpers under each driver = 1/16 step. The firmware expects this.</li></ol>
<figure class="w">{SV.cable_path()}</figure>'''


ASSEMBLY = [
    ('Check the test coupon', 'Bearings press into the pockets with firm thumb pressure: no hammer, and they must not fall out. The printed pins slide into the bearings with a firm push. An M3 nut drops into its hexagon; a screw threads into the small hole. If any fit is wrong, stop and tell the team: one number in the CAD fixes it.', None),
    ('Legs', 'Slide the three legs into the base hub. M4 × 30 bolts from the top, nuts in the hexagons underneath.', 'asm_base'),
    ('Pan bearings', 'Press one 6808 into the top of the base hub and one into the bottom (through the big hole underneath). Press on the outer ring only, with a flat block.', None),
    ('Pan motor', 'Put the 20T pulley on the motor shaft with its hub DOWN, 0.5 mm above the motor face, grub screw on the flat. Push the motor into the tower from below. Two front M3 × 8 screws, loose for now.', 'asm_base'),
    ('Pan turntable', 'Loop the 232 mm belt around the turntable\'s pulley. Lower the hollow spindle down through both bearings and hook the belt over the motor pulley. From underneath: the spindle washer and 3 × M3 × 12. Tighten until there is no play, but the deck still turns freely.', 'asm_exploded'),
    ('Pan belt tension', 'Slide the motor outwards until the belt makes a low "twang" when plucked, then tighten the motor screws.', None),
    ('Pan sensor', 'Press the magnet into the magnet cap (flush with the top). One drop of super glue inside the cap, push it onto the motor shaft tip. Screw the AS5600 under the sensor bridge, chip facing down. Fix the bridge with the two back motor screws (M3 × 35).', 'asm_base'),
    ('Head', 'Camera board on the front plate; front plate on the head. Laser into its holder, holder onto the front plate. Left (hollow) trunnion: 3 × M3 × 10, nuts in the flange. Right trunnion (the one with the pulley): 3 × M3 × 12 from inside the head. Press the tilt magnet into the end of the right trunnion.', 'asm_head'),
    ('Tilt bearings', 'Press one 6806 into each arm, from the inner face (the side with the big pocket).', None),
    ('Head into the arms', 'Hold the head between the arms and slide both arms onto the trunnions. Stand the arms on the deck and bolt them (M4 × 20, nuts in the deck). Push the arms gently towards the head before tightening: no side play, but the head still tilts easily.', 'asm_front'),
    ('Tilt drive', 'Tilt motor onto its stand (4 × M3 × 10, loose) with the 20T pulley, hub towards the stand. Stand onto the deck under the head (2 × M4 × 16, nuts in the deck). Loop the 280 mm belt over the pulley on the right trunnion and the motor pulley. Slide the motor down until the belt twangs, tighten. Tilt sensor bracket on the outside of the right arm, AS5600 in it, chip facing the magnet.', 'asm_head'),
    ('Cables', 'Camera USB and laser wires: out through the left trunnion, down the left arm (cable ties), into the hole in the middle of the deck, down the spindle, out at the bottom of the base. Tilt motor wires go straight into the deck hole (the motor sits right beside it); tilt sensor wires down the right arm. Leave a loose loop above the deck so a ±150° pan never pulls.', None),
    ('Electronics box', 'DC jack, fuse holder and switch into the wall. UNO on the standoffs, CNC shield on top, drivers in X and Y, jumpers in. 12 V wires: jack → fuse → switch → shield terminal. Fan in the lid. TCA9548A and the MOSFET module on their standoffs.', 'asm_desk'),
    ('First power-on', 'Follow "Wiring": check polarity, set Vref, flash the firmware, run the self-test.', None),
]


def sec_assemble(img):
    steps = ''
    for i, (t, d, im) in enumerate(ASSEMBLY):
        pic = f'<img src="{img}{im}.jpg" alt="">' if im else ''
        steps += f'<li class="{"hasimg" if im else ""}"><div><b>{E(t)}</b><p>{E(d)}</p></div>{pic}</li>'
    srows = ''.join(f'<tr><td>{E(a)}</td><td><code>{E(b)}</code></td><td class="c">{n}</td></tr>' for a, b, n in SCREWS)
    return f'''
<figure class="w">{SV.belts()}</figure>
<ol class="asm">{steps}</ol>
<h3>Screws, step by step</h3>
<div class="tw"><table><tr><th>Where</th><th>Screw</th><th>Qty</th></tr>{srows}</table></div>'''


def sec_firmware(prefix):
    return f'''
<p class="lead">One file: <code>rig_firmware_v3.ino</code>. The same protocol as MK2, so the Live page and the laptop software do not change.</p>
<h3>Flash it</h3>
<ol class="steps">
<li>Arduino IDE 2 → Library Manager → install <b>AccelStepper</b>.</li>
<li>Open <code>rig_firmware_v3.ino</code>. Tools → Board → <b>Arduino Uno</b>. Pick the port. Upload.<br>
<span class="m">Or on the Mac: <code>tools/rig/flash.sh urena</code></span></li>
<li>Serial Monitor at 115200. It prints <code># ZeroDrift Mk2 ready, encoders=yes, belts=4:4</code>.
<span class="m">(It still says "Mk2" on purpose: that is how the Live page recognises a stepper rig.)</span></li>
<li>Type <code>!</code> and Enter: the self-test blinks the laser, turns pan +10° and back, and prints <code># encoder saw 10.0x deg</code>.
If it says "direction reversed", flip <code>PAN_ENC_DIR</code> in the file and upload again.</li>
<li>Live page → connect the rig → <b>MK2 DRIVE: "Both belts 20T→80T (4:1)"</b>.</li></ol>
<div class="info"><b>Spare board.</b> The same file runs on the MK2 Nano: change <code>#define BOARD_CNC_SHIELD 1</code> to <code>0</code>.
<b>Python driver:</b> <code>mk2.py</code> needs <code>steps_per_rad</code> × 4 for the belts.</div>
<h3>Try it first in Chrome (Wokwi, free)</h3>
<ol class="steps">
<li>Open <b>wokwi.com/projects/new/arduino-uno</b>.</li>
<li>Paste <code>sketch.ino</code> and <code>diagram.json</code> from the Wokwi folder, and add the library <b>AccelStepper</b>.</li>
<li>Press ▶. Type <code>P3556 T-711</code>: the pan motor turns 400° (= 100° of the rig, because of the belt), tilt −80°.
Type <code>L7.0</code>: the red LED blinks 7 times a second. <code>P999999</code> stops at 150°: the limit works.</li></ol>
<h3>Tested on a PC</h3>
<p>The firmware was compiled on a PC with fake motors, fake sensors and a fake clock, and checked <b>42 times on each board</b>
(UNO + CNC shield, and Nano): travel limits, the 4:1 maths, both sensors over the full ±150° (including the sensor's 0/360 seam),
skipped steps showing up, the laser at exactly 7.00 Hz, junk input, and the self-test (including a sensor mounted the wrong way round).
All pass. Run it again with <code>bash tools/mk3/fwtest/run.sh</code>.</p>'''


TESTS = [
    ('Before printing everything', ['Test coupon: bearings press in firmly, pins slide into the bearings, nut fits, screw holds']),
    ('Mechanics (belts off)', ['Pan turns smoothly by hand, no wobble when you rock the deck', 'Tilt turns smoothly, no side play in the head',
                               'Belts on: a low "twang", teeth fully in the pulleys']),
    ('Electronics (before the motors move)', ['Adapter polarity checked with a multimeter', 'Drivers the right way round (EN to EN)',
                                              'Three jumpers under X and Y', 'Vref set on both drivers', 'Fuse in, switch off, then USB, then 12 V on']),
    ('Firmware', ['Banner says encoders=yes, belts=4:4', 'Self-test: "encoder saw ~10.00 deg"',
                  '"P3556 T-711" then "?" gives about S 3556 -711 E 0', 'After 10 minutes: drivers warm but touchable, E and C still agree']),
    ('Tracking', ['Laser aimed at the camera centre (Live page → SET AIM)', 'Live page drive menu = "Both belts 20T→80T (4:1)"',
                  'Locks on the beacon, ignores the decoy', 'Pan ±150° with no cable pulling']),
]


def sec_tests(web):
    out = ''
    k = 0
    for g, items in TESTS:
        lis = ''
        for it in items:
            k += 1
            lis += (f'<li><label><input type="checkbox" data-k="t{k}"> {E(it)}</label></li>' if web else f'<li><span class="box"></span>{E(it)}</li>')
        out += f'<h3>{E(g)}</h3><ul class="check">{lis}</ul>'
    return '<p class="lead">Tick these in order. Each one catches a mistake before it costs a part.</p>' + out


def sec_downloads():
    items = [('mk3/Plan_Urena.pdf', 'Plan Urena, the whole plan (PDF)'), ('mk3/Plan_Urena_print_shop.pdf', 'Print-shop sheet (PDF)'),
             ('mk3/Plan_Urena_print_pack.zip', 'Print pack: STL + STEP + the sheet (zip, for the pen drive)'),
             ('mk3/firmware/rig_firmware_v3.ino', 'Firmware rig_firmware_v3.ino'),
             ('mk3/wokwi/sketch.ino', 'Wokwi: sketch.ino'), ('mk3/wokwi/diagram.json', 'Wokwi: diagram.json'),
             ('mk3/img/easy_wiring.png', 'Easy wiring picture (PNG)')]
    return '<div class="dl">' + ''.join(f'<a href="{h}" download>{E(t)}</a>' for h, t in items) + '</div>'


# ================================================================== the web page (docs/mk3.html)
WEB_CSS = r'''
@font-face{font-family:'ZD Inter';src:url(fonts/inter-latin-400-normal.woff2) format('woff2');font-weight:400}
@font-face{font-family:'ZD Inter';src:url(fonts/inter-latin-600-normal.woff2) format('woff2');font-weight:600}
@font-face{font-family:'ZD Inter';src:url(fonts/inter-latin-700-normal.woff2) format('woff2');font-weight:700}
:root{--bg:#02050E;--panel:#0A1224;--edge:#15263F;--ink:#EAF4FD;--ink2:#8EA4C4;--mute:#6b80a0;--cyan:#4FC7EA;--green:#3BD68C;--amber:#FFC24D;--red:#FF5C5C;
--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;--sans:'ZD Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--sans)}
a{color:var(--cyan)}
.top{display:flex;align-items:center;gap:14px;padding:12px 16px;border-bottom:1px solid var(--edge);position:sticky;top:0;background:rgba(2,5,14,.94);backdrop-filter:blur(6px);z-index:9}
.top img{height:30px}.top b{font:700 14px var(--mono);letter-spacing:.5px}
.top .badge{font:700 11px var(--mono);letter-spacing:.8px;color:#1a0c00;background:var(--amber);border-radius:6px;padding:4px 8px}
.top nav{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
.top nav a{font:600 11px var(--mono);letter-spacing:.6px;text-decoration:none;color:var(--ink2);border:1px solid var(--edge);border-radius:6px;padding:7px 10px}
.tabs{display:flex;gap:4px;overflow-x:auto;padding:10px 16px;border-bottom:1px solid var(--edge);position:sticky;top:55px;background:rgba(2,5,14,.96);z-index:8;scrollbar-width:none}
.tabs a{flex:none;font:600 12.5px var(--sans);text-decoration:none;color:var(--ink2);padding:8px 13px;border-radius:999px;border:1px solid transparent}
.tabs a:hover{color:var(--ink)}.tabs a.on{color:#04121c;background:var(--cyan)}
main{max-width:1080px;margin:0 auto;padding:22px 16px 80px}
section{display:none}section.on{display:block;animation:fi .25s ease}
@keyframes fi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
h1{font-size:34px;line-height:1.15;margin:6px 0 4px;letter-spacing:-.02em}
h1 small{display:block;font:600 13px var(--mono);letter-spacing:.8px;color:var(--amber);margin-bottom:6px}
h2{font-size:24px;margin:4px 0 12px;letter-spacing:-.01em}
h3{font-size:17px;margin:28px 0 8px;color:var(--cyan)}h3 .sub{float:right;color:var(--ink2);font:600 13px var(--mono)}
p{margin:8px 0}.lead{color:var(--ink2);font-size:16px;max-width:820px}.m,.note{color:var(--mute);font-size:13px}
.hero img{width:100%;max-height:62vh;object-fit:cover;object-position:50% 35%;border-radius:16px;display:block;background:#f3f5f8}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:16px 0}
.fact{background:var(--panel);border:1px solid var(--edge);border-radius:14px;padding:12px 14px}
.fact span{display:block;font:600 11px var(--mono);letter-spacing:.6px;color:var(--ink2);text-transform:uppercase}
.fact b{display:block;font-size:18px;margin:2px 0}.fact em{font-style:normal;color:var(--mute);font-size:12.5px}
.tw{overflow-x:auto;margin:10px 0}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--edge);vertical-align:top}
th{font:600 11px var(--mono);letter-spacing:.6px;color:var(--ink2);text-transform:uppercase;background:var(--panel)}
td.c{text-align:center;width:50px}td.r{text-align:right;white-space:nowrap}
code{font:12.5px var(--mono);background:#0d1a30;border:1px solid var(--edge);border-radius:4px;padding:0 5px}
.where{font:600 11px var(--mono);color:var(--amber);white-space:nowrap}
.tag{display:inline-block;font:700 10.5px var(--mono);letter-spacing:.4px;border-radius:5px;padding:1px 7px;border:1px solid}
.tag.ok{color:var(--green);border-color:rgba(59,214,140,.5)}.tag.no{color:var(--red);border-color:rgba(255,92,92,.5)}.tag.mid{color:var(--amber);border-color:rgba(255,194,77,.55)}
.warn,.ok,.info{border-radius:12px;padding:11px 14px;margin:12px 0;font-size:14px}
.warn{background:rgba(255,92,92,.08);border:1px solid rgba(255,92,92,.45)}.warn b:first-child{color:var(--red)}
.ok{background:rgba(59,214,140,.07);border:1px solid rgba(59,214,140,.4)}.ok b:first-child{color:var(--green)}
.info{background:rgba(79,199,234,.07);border:1px solid rgba(79,199,234,.35)}.info b:first-child{color:var(--cyan)}
figure{margin:14px 0;background:#fff;border-radius:14px;padding:10px;color:#0b1320}
figure img,figure svg{display:block;width:100%;height:auto;border-radius:8px}
figcaption{font-size:12.5px;color:#46566b;padding:6px 4px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.grid2 figure{margin:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
ol.tl{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
ol.tl li{background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:10px 12px}ol.tl b{display:block}ol.tl span{color:var(--ink2);font-size:13px}
ol.steps{padding-left:0;list-style:none;counter-reset:s;margin:10px 0}
ol.steps>li{counter-increment:s;position:relative;padding:10px 12px 10px 48px;margin:8px 0;background:var(--panel);border:1px solid var(--edge);border-radius:12px}
ol.steps>li::before{content:counter(s);position:absolute;left:12px;top:10px;width:24px;height:24px;border-radius:50%;background:var(--cyan);color:#04121c;font:700 12px/24px var(--mono);text-align:center}
ol.asm{list-style:none;padding:0;counter-reset:a}
ol.asm>li{counter-increment:a;display:grid;grid-template-columns:1fr;gap:12px;background:var(--panel);border:1px solid var(--edge);border-radius:14px;padding:14px 14px 14px 58px;margin:10px 0;position:relative}
ol.asm>li.hasimg{grid-template-columns:1fr 260px}
ol.asm>li::before{content:counter(a);position:absolute;left:14px;top:14px;width:30px;height:30px;border-radius:50%;background:var(--amber);color:#1a0c00;font:700 14px/30px var(--mono);text-align:center}
ol.asm img{width:100%;border-radius:10px;background:#f3f5f8}ol.asm p{color:var(--ink2);margin:4px 0 0}
.pcs{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
.pc{display:grid;grid-template-columns:130px 1fr;gap:12px;background:var(--panel);border:1px solid var(--edge);border-radius:14px;padding:10px}
.pc img{width:130px;height:98px;object-fit:contain;background:#fff;border-radius:10px}
.pc code{display:inline-block;margin:2px 0 4px;font-size:11px}.pc p{font-size:13px;color:var(--ink2);margin:2px 0}
.pc dl{display:grid;grid-template-columns:auto 1fr;gap:0 10px;font-size:12.5px;margin:6px 0 0}.pc dt{color:var(--mute)}.pc dd{margin:0}
ul.check{list-style:none;padding:0}ul.check li{padding:7px 10px;border-bottom:1px solid var(--edge)}
ul.check input{width:17px;height:17px;accent-color:var(--green);vertical-align:-3px;margin-right:8px}
.dl{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.dl a{display:block;text-decoration:none;color:var(--ink);background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:14px 16px;font-weight:600}
.dl a::before{content:"↓  ";color:var(--cyan)}
/* 3D */
.v3{display:grid;grid-template-columns:1fr 280px;gap:12px}
#vw{height:min(70vh,640px);border-radius:16px;overflow:hidden;background:#0b0d12;position:relative}
#vw .ld{position:absolute;inset:0;display:grid;place-items:center;color:var(--ink2);font:600 13px var(--mono)}
.ctl{background:var(--panel);border:1px solid var(--edge);border-radius:16px;padding:14px}
.ctl label{display:block;font:600 11px var(--mono);letter-spacing:.6px;color:var(--ink2);margin:10px 0 4px}
.ctl input[type=range]{width:100%;accent-color:var(--cyan)}
.ctl .row{display:flex;gap:6px;flex-wrap:wrap}.ctl button{font:600 12px var(--sans);color:var(--ink);background:#0d1a30;border:1px solid var(--edge);border-radius:8px;padding:6px 10px;cursor:pointer}
.ctl button.on{background:var(--cyan);color:#04121c;border-color:var(--cyan)}
.ctl .cb{display:flex;align-items:center;gap:8px;font:13px var(--sans);color:var(--ink);letter-spacing:0;margin:6px 0}
#pick{margin-top:12px;padding:10px;border-radius:10px;background:#0d1a30;min-height:70px;font-size:13px;color:var(--ink2)}#pick b{color:var(--ink);display:block}
@media(max-width:820px){.v3,.two,.grid2{grid-template-columns:1fr}ol.asm>li.hasimg{grid-template-columns:1fr}.top nav{display:none}}
'''

TABS = [('overview', 'Overview'), ('model', '3D model'), ('print', 'Print'), ('buy', 'Buy'), ('reuse', 'Reuse from MK2'),
        ('camera', 'Camera'), ('wiring', 'Wiring'), ('assemble', 'Assemble'), ('firmware', 'Firmware & sim'), ('tests', 'Tests'),
        ('downloads', 'Downloads')]


def web_page():
    img = 'mk3/img/'
    names = {r['name']: (r['title'], r['what']) for r in print_rows()}
    names['02_leg_2'] = names['02_leg_3'] = names['02_leg_1']
    bought = {'m_pan_motor': ('Pan motor', 'NEMA17 from MK2'), 'm_tilt_motor': ('Tilt motor', 'NEMA17 from MK2'),
              'm_brg_pan_low': ('6808 bearing', 'Lower pan bearing'), 'm_brg_pan_top': ('6808 bearing', 'Upper pan bearing'),
              'm_brg_tilt_r': ('6806 bearing', 'Right tilt bearing'), 'm_brg_tilt_l': ('6806 bearing', 'Left tilt bearing'),
              'm_pan_belt': ('Pan belt', f'GT2 6 mm, 232 mm ({FITS_P[0]}–{FITS_P[-1]} fits)'), 'm_tilt_belt': ('Tilt belt', f'GT2 6 mm, 280 mm ({FITS_T[0]}–{FITS_T[-1]} fits)'),
              'm_pan_pulley20': ('20T pulley', 'Metal, 5 mm bore, hub down'), 'm_tilt_pulley20': ('20T pulley', 'Metal, 5 mm bore'),
              'm_pan_as5600': ('Pan sensor (AS5600)', 'Reads the pan motor shaft'), 'm_tilt_as5600': ('Tilt sensor (AS5600)', 'Reads the magnet in the right trunnion end'),
              'm_camera': ('Camera board', 'USB camera'), 'm_laser': ('Laser', '12 mm, 650 nm, 5 mW')}
    sections = {
        'overview': ('Overview', sec_overview(img)),
        'model': ('3D model', '''<p class="lead">Every part, placed exactly as it fits. Drag to turn, scroll to zoom, click a part to see what it is.</p>
<div class="v3"><div id="vw"><div class="ld">Loading 3D…</div></div>
<div class="ctl"><label>PAN <span id="pv">0°</span></label><input type="range" id="pan" min="-150" max="150" value="0">
<label>TILT <span id="tv">0°</span></label><input type="range" id="tilt" min="-40" max="40" value="0">
<label>EXPLODE</label><input type="range" id="ex" min="0" max="100" value="0">
<label>VIEW</label><div class="row"><button data-v="iso">3D</button><button data-v="front">Front</button><button data-v="side">Side</button><button data-v="top">Top</button><button data-v="head">Head</button><button data-v="base">Base</button></div>
<label>SHOW</label><div class="cb"><input type="checkbox" id="sp" checked> Printed parts</div><div class="cb"><input type="checkbox" id="sb" checked> Bought parts</div><div class="cb"><input type="checkbox" id="sd"> Electronics box</div>
<div class="row" style="margin-top:8px"><button id="auto">▶ Sweep</button></div>
<div id="pick">Click a part.</div></div></div>''' + sec_views(img)),
        'print': ('Print', sec_print(img)), 'buy': ('Buy', sec_buy()), 'reuse': ('Reuse from MK2', sec_reuse()),
        'camera': ('Camera', sec_camera()), 'wiring': ('Wiring', sec_wiring(img)), 'assemble': ('Assemble', sec_assemble(img)),
        'firmware': ('Firmware & simulation', sec_firmware('mk3/')), 'tests': ('Tests', sec_tests(True)), 'downloads': ('Downloads', sec_downloads()),
    }
    tabs = ''.join(f'<a href="#{k}" data-t="{k}">{t}</a>' for k, t in TABS)
    body = ''.join(f'<section id="s-{k}"><h2>{E(sections[k][0])}</h2>{sections[k][1]}</section>' for k, _ in TABS)
    info = json.dumps({**{k: v for k, v in names.items()}, **bought})
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Plan Urena · build</title><link rel="icon" href="brand/zerodrift_mark.png">
<style>{WEB_CSS}</style>
<script type="importmap">{{"imports":{{"three":"./vendor/three/three.module.js","three/addons/controls/OrbitControls.js":"./vendor/three/OrbitControls.js","three/addons/loaders/STLLoader.js":"./vendor/three/STLLoader.js"}}}}</script>
</head><body>
<div class="top"><a href="build.html"><img src="brand/zerodrift_logo.png" alt="ZeroDrift"></a><span class="badge">PLAN URENA</span>
<nav><a href="build.html">MK2 BUILD</a><a href="mk3/Plan_Urena.pdf">PLAN PDF</a><a href="mk3/Plan_Urena_print_shop.pdf">PRINT SHOP</a><a href="live.html">LIVE DEMO</a></nav></div>
<div class="tabs">{tabs}</div>
<main><h1><small>INTERNAL · MK3</small>Plan Urena</h1>{body}</main>
<script>
const INFO={info};
let booted=false;
const tabs=[...document.querySelectorAll('.tabs a')];
function show(k){{if(!document.getElementById('s-'+k))k='overview';
 document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id==='s-'+k));
 tabs.forEach(a=>a.classList.toggle('on',a.dataset.t===k));
 const a=tabs.find(a=>a.dataset.t===k); if(a) a.scrollIntoView({{inline:'center',block:'nearest'}});
 if(k==='model') boot3d(); scrollTo(0,0);}}
addEventListener('hashchange',()=>show(location.hash.slice(1)));show(location.hash.slice(1)||'overview');
document.querySelectorAll('input[data-k]').forEach(c=>{{try{{c.checked=localStorage.getItem('urena_'+c.dataset.k)==='1'}}catch(e){{}}
 c.onchange=()=>{{try{{localStorage.setItem('urena_'+c.dataset.k,c.checked?'1':'0')}}catch(e){{}}}}}});
async function boot3d(){{if(booted)return;booted=true;
 const {{mountViewer}}=await import('./mk3/viewer.js');const el=document.getElementById('vw');
 const V=await mountViewer(el,{{desk:false,onPick:p=>{{const k=p&&p.name;const d=INFO[k]||(p?[k,p.note||'']:null);
  document.getElementById('pick').innerHTML=d?'<b>'+d[0]+'</b>'+d[1]+(p.printed?'<br><code>'+k+'.stl</code>':''):'Click a part.';}},
  onPose:(a,b)=>{{pan.value=a;tilt.value=b;pv.textContent=Math.round(a)+'°';tv.textContent=Math.round(b)+'°';}}}});
 el.querySelector('.ld').remove();
 const $=id=>document.getElementById(id);const pan=$('pan'),tilt=$('tilt'),pv=$('pv'),tv=$('tv');
 pan.oninput=()=>{{V.set('auto',false);$('auto').classList.remove('on');V.set('pan',+pan.value);pv.textContent=pan.value+'°'}};
 tilt.oninput=()=>{{V.set('auto',false);$('auto').classList.remove('on');V.set('tilt',+tilt.value);tv.textContent=tilt.value+'°'}};
 let wide=false;$('ex').oninput=e=>{{V.set('explode',e.target.value/100);if(e.target.value>30&&!wide){{wide=true;V.view('wide')}}}};
 $('sp').onchange=e=>V.set('showPrinted',e.target.checked);$('sb').onchange=e=>V.set('showBought',e.target.checked);$('sd').onchange=e=>V.set('desk',e.target.checked);
 document.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>V.view(b.dataset.v));
 $('auto').onclick=e=>{{const on=!V.state.auto;V.set('auto',on);e.target.classList.toggle('on',on)}};}}
</script></body></html>'''


# ================================================================== the Plan PDF (docs/mk3/plan.html)
PDF_CSS = r'''
@font-face{font-family:'ZD Inter';src:url(../fonts/inter-latin-400-normal.woff2) format('woff2');font-weight:400}
@font-face{font-family:'ZD Inter';src:url(../fonts/inter-latin-600-normal.woff2) format('woff2');font-weight:600}
@font-face{font-family:'ZD Inter';src:url(../fonts/inter-latin-700-normal.woff2) format('woff2');font-weight:700}
@font-face{font-family:'ZD Inter';src:url(../fonts/inter-latin-800-normal.woff2) format('woff2');font-weight:800}
@page{size:A4;margin:14mm 13mm 16mm}
*{box-sizing:border-box}
body{margin:0;font:10pt/1.5 'ZD Inter',Helvetica,Arial,sans-serif;color:#1d1d1f;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.cover{height:265mm;display:flex;flex-direction:column;page-break-after:always}
.cover .k{font:700 9pt 'ZD Inter';letter-spacing:.14em;color:#b86e00}
.cover h1{font-size:44pt;line-height:1;margin:6mm 0 3mm;letter-spacing:-.03em;font-weight:800}
.cover p{font-size:13pt;color:#515154;max-width:150mm;margin:0}
.cover img{width:100%;margin:10mm 0 6mm;border-radius:5mm}
.cover .toc{columns:2;font-size:10pt;margin-top:auto}.cover .toc div{padding:1.2mm 0;border-bottom:.3mm solid #e5e5ea}
.cover .toc b{display:inline-block;width:8mm;color:#b86e00}
section{page-break-before:always}
h2{font-size:22pt;margin:0 0 3mm;letter-spacing:-.02em;font-weight:800}h2 .n{color:#b86e00;font-size:12pt;display:block;letter-spacing:.1em;font-weight:700}
h3{font-size:12.5pt;margin:6mm 0 2mm;break-after:avoid}h3 .sub{float:right;color:#6e6e73;font-size:10pt}
p{margin:1.5mm 0}.lead{font-size:11.5pt;color:#3a3a3c}.m,.note{color:#6e6e73;font-size:9pt}
.hero img{width:100%;height:78mm;object-fit:cover;object-position:50% 35%;border-radius:4mm}
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:2.5mm;margin:4mm 0}
.fact{background:#f5f5f7;border-radius:3mm;padding:2.5mm 3mm;break-inside:avoid}.fact span{display:block;font-size:7pt;letter-spacing:.08em;color:#6e6e73;text-transform:uppercase;font-weight:700}
.fact b{display:block;font-size:11pt}.fact em{font-style:normal;color:#6e6e73;font-size:8pt}
table{width:100%;border-collapse:collapse;font-size:9pt;margin:2mm 0}tr{break-inside:avoid}
th,td{text-align:left;padding:1.6mm 2mm;border-bottom:.3mm solid #e5e5ea;vertical-align:top}
th{font-size:7.5pt;letter-spacing:.06em;text-transform:uppercase;color:#6e6e73;background:#f5f5f7}
td.c{text-align:center}td.r{text-align:right;white-space:nowrap}
code{font:8.5pt ui-monospace,Menlo,monospace;background:#f2f2f5;border-radius:1mm;padding:0 1mm}
.where{font-size:8pt;font-weight:700;color:#b86e00;white-space:nowrap}
.tag{font-size:7.5pt;font-weight:700;border-radius:1mm;padding:0 1.5mm;border:.3mm solid}.tag.ok{color:#248a3d}.tag.no{color:#d70015}.tag.mid{color:#b86e00}
.warn,.ok,.info{border-radius:3mm;padding:2.5mm 3.5mm;margin:3mm 0;font-size:9.5pt;break-inside:avoid}
.warn{background:#fff1f0}.warn b:first-child{color:#d70015}.ok{background:#effaf2}.ok b:first-child{color:#248a3d}.info{background:#eef6ff}.info b:first-child{color:#0a64c8}
figure{margin:3mm 0;break-inside:avoid}figure img,figure svg{width:100%;height:auto;display:block;border-radius:2mm}
figcaption{font-size:8.5pt;color:#6e6e73;margin-top:1mm}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:3mm}.grid2 figure{margin:0;background:#f3f5f8;border-radius:3mm;overflow:hidden}
.two{display:grid;grid-template-columns:1fr 1fr;gap:5mm;align-items:start}
ol.tl{list-style:none;padding:0;display:grid;grid-template-columns:repeat(3,1fr);gap:2.5mm}ol.tl li{background:#f5f5f7;border-radius:3mm;padding:2.5mm 3mm}ol.tl b{display:block}ol.tl span{font-size:9pt;color:#515154}
ol.steps{padding-left:5mm;margin:2mm 0}ol.steps li{margin:1mm 0;break-inside:avoid}
ol.asm{list-style:none;padding:0;counter-reset:a}
ol.asm>li{counter-increment:a;display:grid;grid-template-columns:1fr;gap:4mm;padding:2.5mm 0 2.5mm 11mm;border-bottom:.3mm solid #e5e5ea;position:relative;break-inside:avoid}
ol.asm>li.hasimg{grid-template-columns:1fr 55mm}
ol.asm>li::before{content:counter(a);position:absolute;left:0;top:2.5mm;width:7.5mm;height:7.5mm;border-radius:50%;background:#ff9f0a;color:#1d1d1f;font:700 10pt/7.5mm 'ZD Inter';text-align:center}
ol.asm img{width:100%;border-radius:2mm;background:#f3f5f8}ol.asm p{margin:1mm 0 0;color:#3a3a3c}
.pcs{display:grid;grid-template-columns:1fr 1fr;gap:3mm}
.pc{display:grid;grid-template-columns:32mm 1fr;gap:3mm;background:#f5f5f7;border-radius:3mm;padding:2.5mm;break-inside:avoid}
.pc img{width:32mm;height:24mm;object-fit:contain;background:#fff;border-radius:2mm}.pc b{font-size:10pt}
.pc code{display:inline-block;font-size:7.5pt;margin-left:1.5mm}.pc p{font-size:8.5pt;color:#3a3a3c;margin:.5mm 0}
.pc dl{display:grid;grid-template-columns:auto 1fr;gap:0 2.5mm;font-size:8pt;margin:1mm 0 0}.pc dt{color:#6e6e73}.pc dd{margin:0}
ul.check{list-style:none;padding:0;margin:1mm 0}ul.check li{padding:1.6mm 0;border-bottom:.3mm solid #e5e5ea;break-inside:avoid}
.box{display:inline-block;width:3.8mm;height:3.8mm;border:.4mm solid #1d1d1f;border-radius:.8mm;margin-right:2.5mm;vertical-align:-.7mm}
.w{background:#fff}
'''

PDF_SECTIONS = [('overview', 'The plan'), ('views', 'The design'), ('buy', 'What to buy'), ('reuse', 'Reuse from MK2'),
                ('print', 'Printed parts'), ('camera', 'Camera options'), ('wiring', 'Wiring and power'),
                ('assemble', 'Assembly'), ('firmware', 'Firmware and simulation'), ('tests', 'Tests')]


def pdf_plan():
    img = 'img/'
    fn = {'overview': lambda: sec_overview(img), 'views': lambda: sec_views(img), 'buy': sec_buy, 'reuse': sec_reuse,
          'print': lambda: sec_print(img, True), 'camera': sec_camera, 'wiring': lambda: sec_wiring(img),
          'assemble': lambda: sec_assemble(img), 'firmware': lambda: sec_firmware(''), 'tests': lambda: sec_tests(False)}
    toc = ''.join(f'<div><b>{i + 1:02d}</b>{t}</div>' for i, (_, t) in enumerate(PDF_SECTIONS))
    body = ''.join(f'<section><h2><span class="n">{i + 1:02d}</span>{t}</h2>{fn[k]()}</section>' for i, (k, t) in enumerate(PDF_SECTIONS))
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow"><title>Plan Urena</title><style>{PDF_CSS}</style></head><body>
<div class="cover"><div class="k">INTERNAL · TEAM ZERODRIFT · SIH 2026</div><h1>Plan Urena</h1>
<p>The MK3 pan-tilt: 3D-printed, belt-driven, on hollow bearings. What to buy, what to print, how to wire it and how to build it.</p>
<img src="img/asm_iso.jpg" alt=""><div class="toc">{toc}</div></div>{body}</body></html>'''


# ================================================================== the print-shop sheet (docs/mk3/print_shop.html)
def pdf_print_shop():
    rows = print_rows()
    trs = ''
    for r in rows:
        qty = 3 if r['name'] == '02_leg_1' else r['qty']
        fname = '02_leg_1, 02_leg_2, 02_leg_3' if r['name'] == '02_leg_1' else r['name']
        note = f'<br><span class=m>{E(r["note"])}</span>' if r['note'] else ''
        size = ' × '.join(f'{v:.0f}' for v in r['bbox'])
        grams = r['grams'] * (qty if r['name'] == '02_leg_1' else 1)
        trs += (f'<tr><td><img src="img/parts/{r["img"]}.jpg" style="width:24mm;height:18mm;object-fit:contain;background:#fff"></td>'
                f'<td><b>{E(r["title"])}</b><br><code>{fname}.stl</code>{note}</td>'
                f'<td class="c">{qty}</td><td>{size}</td><td class="r">{g_(grams)}</td>'
                f'<td>{E(r["colour"])}</td><td>{E(r["supports"])}</td></tr>')
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow"><title>Plan Urena · print shop</title><style>{PDF_CSS}
table td{{vertical-align:middle}}</style></head><body>
<h2><span class="n">FOR THE PRINT SHOP</span>3D printing job: 20 files, ≈{GRAMS:,} g PETG</h2>
<p class="lead">Hello! These are parts for a student robotics project (Team ZeroDrift, Jabalpur Engineering College).
Please print the <b>test coupon first</b>; we will check it and confirm before you print the rest.</p>
<figure>{SV.pendrive()}</figure>
<h3>Settings for every part</h3>
<table>
<tr><td><b>Material</b></td><td>PETG. Black for: head, front plate, laser holder. Any colour for the rest (grey preferred).</td></tr>
<tr><td><b>Layers / nozzle</b></td><td>0.2 mm layers, 0.4 mm nozzle</td></tr>
<tr><td><b>Walls / top / bottom</b></td><td>4 walls, 5 top, 5 bottom</td></tr>
<tr><td><b>Infill</b></td><td>40 % gyroid</td></tr>
<tr><td><b>Supports</b></td><td>None, except inside the motor pocket of 01_base_hub</td></tr>
<tr><td><b>Orientation</b></td><td>Keep as in the files. Every part is already placed flat on the bed.</td></tr>
<tr><td><b>Scale</b></td><td>100 %. Please do not rescale: the bearing holes are exact.</td></tr>
<tr><td><b>Brim</b></td><td>01_base_hub and 16_electronics_box</td></tr>
</table>
<div class="info"><b>Fit check.</b> The test coupon has two bearing holes (52 and 42 mm) and two rings (40 and 30 mm).
If your printer runs a little big or small, tell us the measured sizes. We can adjust the files, or you can set horizontal expansion.</div>
<section><h3>The parts</h3>
<table><tr><th></th><th>Part / file</th><th>Qty</th><th>Size (mm)</th><th>PETG</th><th>Colour</th><th>Supports</th></tr>{trs}
<tr><td></td><td><b>Total</b></td><td class="c">22</td><td></td><td class="r"><b>≈{GRAMS:,} g</b></td><td></td><td></td></tr></table>
<p class="m">Contact: Team ZeroDrift. Please quote one price for the whole job.</p></section>
</body></html>'''


PACK_README = '''Plan Urena print pack (Team ZeroDrift)
=====================================
1_PRINT_FIRST/00_test_coupon.stl   print this first; we check the fits
2_STL/                             every part, already placed flat on the bed (print these)
3_STEP/                            the same parts as STEP, only for editing
Plan_Urena_print_shop.pdf          settings and the parts list with pictures

Settings: PETG, 0.2 mm layers, 0.4 mm nozzle, 4 walls, 5 top/bottom, 40 % gyroid.
Supports: none, except inside the motor pocket of 01_base_hub. Brim on 01_base_hub and 16_electronics_box.
Black: 11_head, 12_front_plate, 13_laser_holder. Scale 100 %, do not rescale.
Print 02_leg_1, 02_leg_2, 02_leg_3 (three legs). Everything else: one each (04_magnet_cap: two if easy).
'''


def main():
    open(os.path.join(DOCS, 'mk3.html'), 'w').write(web_page())
    open(os.path.join(MK3, 'plan.html'), 'w').write(pdf_plan())
    open(os.path.join(MK3, 'print_shop.html'), 'w').write(pdf_print_shop())
    # firmware + Wokwi copies for the downloads tab
    os.makedirs(os.path.join(MK3, 'firmware'), exist_ok=True)
    os.makedirs(os.path.join(MK3, 'wokwi'), exist_ok=True)
    shutil.copy(os.path.join(REPO, 'tools', 'rig', 'rig_firmware_v3.ino'), os.path.join(MK3, 'firmware', 'rig_firmware_v3.ino'))
    for f in ('sketch.ino', 'diagram.json', 'libraries.txt', 'README.md'):
        shutil.copy(os.path.join(ROOT, 'wokwi', f), os.path.join(MK3, 'wokwi', f))
    print('pages written;', f'buy {rng(BUY_LO, BUY_HI)}, print {rng(PR_LO, PR_HI)}, {GRAMS} g')


def pack():
    """after the PDFs exist: the zip for the pen drive"""
    z = os.path.join(MK3, 'Plan_Urena_print_pack.zip')
    out = os.path.join(ROOT, 'out')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('PlanUrena_print/README.txt', PACK_README)
        zf.write(os.path.join(out, 'print', '00_test_coupon.stl'), 'PlanUrena_print/1_PRINT_FIRST/00_test_coupon.stl')
        for f in sorted(os.listdir(os.path.join(out, 'print'))):
            zf.write(os.path.join(out, 'print', f), 'PlanUrena_print/2_STL/' + f)
        for f in sorted(os.listdir(os.path.join(out, 'step'))):
            zf.write(os.path.join(out, 'step', f), 'PlanUrena_print/3_STEP/' + f)
        zf.write(os.path.join(MK3, 'Plan_Urena_print_shop.pdf'), 'PlanUrena_print/Plan_Urena_print_shop.pdf')
    print('pack', round(os.path.getsize(z) / 1e6, 1), 'MB')


if __name__ == '__main__':
    import sys
    pack() if 'pack' in sys.argv else main()
