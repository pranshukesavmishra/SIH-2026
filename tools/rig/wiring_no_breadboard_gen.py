"""MK2 wiring without a breadboard: one high-resolution sheet.
Pins follow tools/rig/rig_firmware_v2.ino (pan STEP/DIR D2/D3, tilt D4/D5, laser D7)."""
W, H = 2000, 1930
C12, CG, C5 = '#dc2626', '#111827', '#ea8a00'
CSTEP, CDIR, CLAS = '#7c3aed', '#0284c7', '#16a34a'
CPA, CPB = '#0d9488', '#db2777'
SANS = "font-family='Liberation Sans, DejaVu Sans, Arial, sans-serif'"
MONO = "font-family='DejaVu Sans Mono, Liberation Mono, monospace'"
o = []
a = o.append


def t(x, y, s, size=14, fill='#0f172a', w=400, anchor='start', mono=False, extra=''):
    a(f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{w}' fill='{fill}' text-anchor='{anchor}' "
      f"{MONO if mono else SANS} {extra}>{s}</text>")


def line(pts, col, wd=5, dash=None):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    a(f"<path d='{d}' fill='none' stroke='{col}' stroke-width='{wd}' stroke-linejoin='round' stroke-linecap='round'"
      + (f" stroke-dasharray='{dash}'" if dash else '') + "/>")


def wire(pts, col, hops=()):
    """Orthogonal wire with a white under-stroke; hops = x positions on horizontal runs to bridge."""
    d = f'M{pts[0][0]} {pts[0][1]}'
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 == y1:
            for hx in sorted(hops, reverse=x1 < x0):
                if min(x0, x1) < hx < max(x0, x1):
                    s = 1 if x1 > x0 else -1
                    d += f' L{hx - 9 * s} {y0} A9 9 0 0 {1 if s > 0 else 0} {hx + 9 * s} {y0}'
        d += f' L{x1} {y1}'
    for col_, wd in (('#ffffff', 10), (col, 5)):
        a(f"<path d='{d}' fill='none' stroke='{col_}' stroke-width='{wd}' stroke-linejoin='round' stroke-linecap='round'/>")


def badge(x, y, n, col):
    a(f"<circle cx='{x}' cy='{y}' r='17' fill='{col}' stroke='#fff' stroke-width='3'/>")
    t(x, y + 5, f'W{n}', 12, '#fff', 700, 'middle')


def tag(x, y, txt, col, right=True):
    """Label at the end of a wire stub. x = stub end; box grows away from the pin."""
    wbox = 12 + len(txt) * 8.2
    bx = x if right else x - wbox
    a(f"<rect x='{bx}' y='{y - 13}' width='{wbox}' height='26' rx='6' fill='#fff' stroke='{col}' stroke-width='2.2'/>")
    t(bx + wbox / 2, y + 5, txt, 13.5, col, 700, 'middle', mono=True)


def pin(x, y, used=None):
    if used:
        a(f"<circle cx='{x}' cy='{y}' r='8' fill='{used}' stroke='#fde68a' stroke-width='2.5'/>")
    else:
        a(f"<circle cx='{x}' cy='{y}' r='6' fill='#d6b35a' stroke='#8a6d1f' stroke-width='1.5'/>")


def panel(y, h, num, title, sub):
    a(f"<rect x='30' y='{y}' width='{W - 60}' height='{h}' rx='22' fill='#ffffff' stroke='#cbd5e1' stroke-width='2'/>")
    a(f"<rect x='30' y='{y}' width='64' height='54' rx='14' fill='#0b1f3a'/>")
    t(62, y + 37, num, 26, '#fff', 700, 'middle')
    t(110, y + 36, title, 25, '#0b1f3a', 700)
    t(124 + len(title) * 15.5, y + 36, sub, 16, '#475569', 400)


# ---------------------------------------------------------------- canvas
a(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>")
a("<defs><pattern id='grid' width='24' height='24' patternUnits='userSpaceOnUse'><path d='M24 0H0V24' fill='none' stroke='#e2e8f0' stroke-width='1'/></pattern>"
  "<linearGradient id='pcbB' x1='0' x2='1'><stop offset='0' stop-color='#1d4f9c'/><stop offset='1' stop-color='#2563c4'/></linearGradient>"
  "<linearGradient id='pcbR' x1='0' x2='1'><stop offset='0' stop-color='#b91c1c'/><stop offset='1' stop-color='#dc2626'/></linearGradient>"
  "<linearGradient id='alu' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#e5e7eb'/><stop offset='1' stop-color='#9ca3af'/></linearGradient>"
  "<linearGradient id='mot' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#4b5563'/><stop offset='1' stop-color='#1f2937'/></linearGradient>"
  "<filter id='sh' x='-10%' y='-10%' width='130%' height='130%'><feDropShadow dx='0' dy='6' stdDeviation='7' flood-color='#0f172a' flood-opacity='.22'/></filter></defs>")
a(f"<rect width='{W}' height='{H}' fill='#f1f5f9'/><rect width='{W}' height='{H}' fill='url(#grid)'/>")

# header
a(f"<rect x='0' y='0' width='{W}' height='96' fill='#0b1f3a'/>")
t(40, 46, 'ZeroDrift MK2 · wiring WITHOUT a breadboard', 34, '#fff', 700)
t(40, 78, 'Every wire has a number (W1–W22). Wire with EVERYTHING unplugged. Tick each wire in section ③ when it is done.', 17, '#bcd3ee')
t(W - 40, 46, 'pins match rig_firmware_v2.ino', 16, '#7dd3fc', 700, 'end', mono=True)
t(W - 40, 76, 'pan D2/D3 · tilt D4/D5 · laser D7', 16, '#7dd3fc', 400, 'end', mono=True)

# ================================================================ ① POWER
panel(112, 372, '1', 'Power', '   12 V only to the drivers · 5 V from the Nano · one shared GND')

# adapter
a("<g filter='url(#sh)'><rect x='64' y='214' width='176' height='96' rx='14' fill='#1f2937'/></g>")
t(152, 256, '12 V · 2 A', 20, '#fff', 700, 'middle'); t(152, 282, 'wall adapter', 14, '#cbd5e1', 400, 'middle')
line([(240, 262), (292, 262)], '#111', 9)
a("<rect x='286' y='250' width='22' height='24' rx='4' fill='#6b7280'/>")
t(152, 200, 'plug it in LAST', 13, '#b91c1c', 700, 'middle')

# DC jack, 3 legs
a("<g filter='url(#sh)'><rect x='308' y='208' width='150' height='112' rx='12' fill='#27272a'/></g>")
a("<circle cx='383' cy='250' r='26' fill='#0a0a0a' stroke='#52525b' stroke-width='4'/><circle cx='383' cy='250' r='6' fill='#d4d4d8'/>")
t(383, 305, 'DC JACK', 13, '#e4e4e7', 700, 'middle')
for x, lab, col in ((338, 'empty', '#64748b'), (383, '− sleeve', CG), (428, '+ pin', C12)):
    a(f"<rect x='{x - 4}' y='320' width='8' height='30' fill='#cbd5e1' stroke='#64748b'/>")
t(338, 372, 'leave', 12, '#64748b', 700, 'middle'); t(338, 386, 'empty', 12, '#64748b', 700, 'middle')
t(383, 184, 'Check first with a multimeter:', 13, '#334155', 700, 'middle')
t(383, 200, '+ leg reads +12 V to the − leg', 13, '#334155', 400, 'middle')

# toggle switch
a("<g filter='url(#sh)'><rect x='560' y='222' width='140' height='88' rx='12' fill='#334155'/></g>")
a("<rect x='620' y='204' width='20' height='34' rx='8' fill='#cbd5e1' stroke='#64748b' stroke-width='2' transform='rotate(22 630 236)'/>")
t(630, 290, 'KILL SWITCH', 13, '#f1f5f9', 700, 'middle')
for x in (590, 630, 670):
    a(f"<rect x='{x - 4}' y='310' width='8' height='30' fill='#cbd5e1' stroke='#64748b'/>")
t(590, 362, 'empty', 12, '#64748b', 700, 'middle')
t(630, 172, 'OUT = outer leg that beeps', 13, '#334155', 400, 'middle')
t(630, 188, 'to MIDDLE when switch is ON', 13, '#334155', 700, 'middle')

# power wires
wire([(428, 350), (428, 372), (630, 372), (630, 340)], C12); badge(530, 372, 1, C12)
wire([(670, 340), (670, 400), (770, 400), (770, 206), (806, 206)], C12); badge(770, 300, 2, C12)
wire([(383, 350), (383, 452), (1180, 452), (1180, 206), (1212, 206)], CG); badge(800, 452, 3, CG)


def bus(x, y0, rows, col, name, note):
    n = len(rows)
    a(f"<g filter='url(#sh)'><rect x='{x}' y='{y0 - 24}' width='62' height='{n * 38 + 10}' rx='10' fill='#f8fafc' stroke='{col}' stroke-width='3'/></g>")
    t(x + 31, y0 - 36, name, 16, col, 700, 'middle')
    for i, (lab, inp) in enumerate(rows):
        y = y0 + i * 38
        a(f"<rect x='{x + 8}' y='{y - 9}' width='26' height='18' rx='4' fill='#f59e0b' stroke='#b45309'/>")
        a(f"<rect x='{x + 38}' y='{y - 6}' width='18' height='12' rx='2' fill='#cbd5e1'/>")
        if lab:
            line([(x + 62, y), (x + 86, y)], col, 5)
            t(x + 94, y + 5, lab, 14.5, '#0f172a' if not inp else col, 700, mono=True)
    t(x + 31, y0 + n * 38 + 6, note, 12, '#64748b', 400, 'middle')


bus(806, 206, [('W2  ◀ from switch OUT', True), ('W4  ▶ PAN  driver VMOT', False), ('W5  ▶ TILT driver VMOT', False)],
    C12, '12 V BUS', '')
bus(1212, 206, [('W3  ◀ from jack − (sleeve)', True), ('W6  ▶ PAN  driver GND*', False), ('W7  ▶ TILT driver GND*', False),
                ('W8  ▶ Nano GND', False), ('W14 ▶ PAN  driver EN', False), ('W15 ▶ TILT driver EN', False),
                ('W22 ▶ laser −', False)], CG, 'GND BUS', '')
bus(1600, 206, [('W9  ◀ from Nano 5V pin', True), ('W10 ▶ PAN  driver VDD', False), ('W11 ▶ TILT driver VDD', False),
                ('W12 ▶ PAN  MS1·MS2·MS3', False), ('W13 ▶ TILT MS1·MS2·MS3', False), ('W21 ▶ laser + (middle)', False),
                ('spare: AS5600 later', False)], C5, '5 V BUS', '')
t(806, 350, 'BUS = a WAGO lever block,', 13, '#475569', 700)
t(806, 368, 'or all wires twisted + soldered', 13, '#475569', 400)
t(806, 386, '+ heat-shrink. Never bare.', 13, '#475569', 400)
t(1330, 476, '* the GND pin right beside VMOT', 12.5, '#475569', 400)
t(806, 418, '12 V must NEVER touch the', 13.5, C12, 700)
t(806, 436, '5 V bus, the Nano or VDD.', 13.5, C12, 700)

# ================================================================ ② CONTROL + MOTORS
PY = 506
panel(PY, 876, '2', 'Nano → drivers → motors', '   Drawn from the top. Pin names are also printed on each board: match them.')

# ---- Nano
NX0, NX1, NY0 = 262, 422, 590
a(f"<g filter='url(#sh)'><rect x='{NX0}' y='{NY0}' width='160' height='520' rx='10' fill='url(#pcbB)'/></g>")
a(f"<rect x='{NX0 + 50}' y='{NY0 - 22}' width='60' height='36' rx='5' fill='url(#alu)' stroke='#6b7280'/>")
t(NX0 - 12, NY0 - 2, 'USB → laptop', 14, '#0f172a', 700, 'end')
t(NX0 + 80, NY0 + 260, 'ARDUINO  NANO', 17, '#dbeafe', 700, 'middle', extra=f"transform='rotate(-90 {NX0 + 80} {NY0 + 260})' letter-spacing='3'")
R = ['D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'GND', 'RST', 'RX0', 'TX1']
L = ['D13', '3V3', 'REF', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', '5V', 'RST', 'GND', 'VIN']
NP = {}
used_r = {'D7': CLAS, 'D5': CDIR, 'D4': CSTEP, 'D3': CDIR, 'D2': CSTEP}
used_l = {'5V': C5, 'GND': CG}
for i, (l, r) in enumerate(zip(L, R)):
    y = NY0 + 40 + i * 30
    pin(NX0 + 15, y, used_l.get(l) if (l != 'GND' or i == 13) else None)
    pin(NX1 - 15, y, used_r.get(r))
    t(NX0 + 30, y + 5, l, 12.5, '#fff' if l in used_l and (l != 'GND' or i == 13) else '#bfdbfe', 700 if l in used_l else 400, mono=True)
    t(NX1 - 30, y + 5, r, 12.5, '#fff' if r in used_r else '#bfdbfe', 700 if r in used_r else 400, 'end', mono=True)
    NP['L' + l + str(i)] = y; NP['R' + r] = y
yD7, yD5, yD4, yD3, yD2 = NP['RD7'], NP['RD5'], NP['RD4'], NP['RD3'], NP['RD2']
y5V, yGN = NP['L5V11'], NP['LGND13']
# Nano power tags (left side)
line([(NX0 + 15, y5V), (NX0 - 34, y5V)], C5, 5); tag(NX0 - 34, y5V, 'W9 → 5 V bus', C5, right=False)
line([(NX0 + 15, yGN), (NX0 - 34, yGN)], CG, 5); tag(NX0 - 34, yGN, 'W8 → GND bus', CG, right=False)
t(NX0 + 80, NY0 + 548, 'the other GND pin: empty', 12, '#64748b', 400, 'middle')

# ---- laser KY-008
LX, LY = 470, 590
a(f"<g filter='url(#sh)'><rect x='{LX}' y='{LY}' width='150' height='50' rx='6' fill='#18181b'/></g>")
a(f"<rect x='{LX + 150}' y='{LY + 14}' width='40' height='22' rx='4' fill='url(#alu)'/><circle cx='{LX + 192}' cy='{LY + 25}' r='6' fill='#ef4444'/>")
t(LX + 75, LY - 10, 'KY-008 laser', 14, '#0f172a', 700, 'middle')
for x, lab in ((LX + 25, 'S'), (LX + 65, '+'), (LX + 105, '−')):
    a(f"<rect x='{x - 4}' y='{LY + 50}' width='8' height='20' fill='#d6b35a' stroke='#8a6d1f'/>")
    t(x, LY + 36, lab, 15, '#fff', 700, 'middle')
wire([(NX1 - 15, yD7), (LX + 25, yD7), (LX + 25, LY + 70)], CLAS); badge(LX + 25, (yD7 + LY + 70) // 2 + 6, 20, CLAS)
line([(LX + 105, LY + 70), (LX + 105, LY + 88), (LX + 135, LY + 88)], CG, 5); tag(LX + 135, LY + 88, 'W22 GND bus', CG)
line([(LX + 65, LY + 70), (LX + 65, LY + 116), (LX + 135, LY + 116)], C5, 5); tag(LX + 135, LY + 116, 'W21 5 V bus', C5)


# ---- A4988 drivers
def driver(x, y0, name, cap):
    a(f"<g filter='url(#sh)'><rect x='{x}' y='{y0}' width='200' height='290' rx='8' fill='url(#pcbR)'/></g>")
    t(x + 100, y0 - 12, name, 17, '#0f172a', 700, 'middle')
    # heat sink + pot
    a(f"<rect x='{x + 62}' y='{y0 + 92}' width='76' height='76' rx='4' fill='url(#alu)' stroke='#6b7280'/>")
    for k in range(6):
        a(f"<rect x='{x + 68 + k * 12}' y='{y0 + 96}' width='5' height='68' fill='#9ca3af'/>")
    a(f"<circle cx='{x + 100}' cy='{y0 + 222}' r='15' fill='#e5e7eb' stroke='#6b7280' stroke-width='2'/><path d='M{x + 92} {y0 + 222}h16M{x + 100} {y0 + 214}v16' stroke='#374151' stroke-width='3'/>")
    t(x + 100, y0 + 256, 'Vref 0.55 V', 12, '#fee2e2', 700, 'middle')
    t(x + 100, y0 + 276, 'A4988', 14, '#fff', 700, 'middle')
    LP = ['EN', 'MS1', 'MS2', 'MS3', 'RST', 'SLP', 'STEP', 'DIR']
    RP = ['VMOT', 'GND', '2B', '2A', '1A', '1B', 'VDD', 'GND']
    P = {}
    for i in range(8):
        y = y0 + 40 + i * 30
        P['L' + LP[i]] = y; P['R' + RP[i] + ('2' if i == 7 else '')] = y
        pin(x + 15, y, {'EN': CG, 'MS1': C5, 'MS2': C5, 'MS3': C5, 'STEP': CSTEP, 'DIR': CDIR}.get(LP[i]))
        pin(x + 185, y, {'VMOT': C12, 'GND': CG, '2B': CPA, '2A': CPA, '1A': CPB, '1B': CPB, 'VDD': C5}.get(RP[i]) if i != 7 else None)
        t(x + 30, y + 5, LP[i], 12.5, '#fff', 700, mono=True)
        t(x + 170, y + 5, RP[i], 12.5, '#fff', 700, 'end', mono=True)
    # solder bridges MS1-MS3 and RST-SLP
    for y1, y2 in ((P['LMS1'], P['LMS3']), (P['LRST'], P['LSLP'])):
        a(f"<rect x='{x + 5}' y='{y1 - 11}' width='20' height='{y2 - y1 + 22}' rx='10' fill='#c0c0c0' stroke='#4b5563' stroke-width='2' opacity='.95'/>")
    # capacitor across VMOT / GND, right at the pins
    cx = x + 222
    line([(x + 185, P['RVMOT']), (cx + 60, P['RVMOT'])], C12, 5)
    line([(x + 185, P['RGND']), (cx + 60, P['RGND'])], CG, 5)
    a(f"<rect x='{cx - 12}' y='{P['RVMOT'] - 3}' width='24' height='{P['RGND'] - P['RVMOT'] + 6}' rx='6' fill='#1e3a8a' stroke='#0f172a' stroke-width='1.5'/>")
    a(f"<rect x='{cx - 12}' y='{(P['RVMOT'] + P['RGND']) // 2 + 2}' width='24' height='{(P['RGND'] - P['RVMOT']) // 2 + 1}' rx='5' fill='#cbd5e1'/>")
    t(cx, (P['RVMOT'] + P['RGND']) // 2 + 14, '−', 13, '#111', 700, 'middle')
    t(cx, P['RVMOT'] - 12, cap, 13, '#1e3a8a', 700, 'middle')
    return P


TX, TY = 700, 722          # TILT driver on top (it takes D4/D5, which sit above D2/D3 on the Nano)
PXx, PYy = 700, 1052
T = driver(TX, TY, 'TILT driver (A4988)', 'C2')
Pn = driver(PXx, PYy, 'PAN driver (A4988)', 'C1')

# left-side tags on each driver
for P, x, en, ms in ((T, TX, 'W15 GND bus', 'W13 5 V bus'), (Pn, PXx, 'W14 GND bus', 'W12 5 V bus')):
    line([(x + 15, P['LEN']), (x - 30, P['LEN'])], CG, 5); tag(x - 30, P['LEN'], en, CG, right=False)
    line([(x + 15, P['LMS1']), (x - 30, P['LMS1'])], C5, 5); tag(x - 30, P['LMS1'], ms, C5, right=False)

# STEP / DIR from the Nano (one crossing per pair, bridged)
wire([(NX1 - 15, yD5), (662, yD5), (662, T['LDIR']), (TX + 15, T['LDIR'])], CDIR)
wire([(NX1 - 15, yD4), (640, yD4), (640, T['LSTEP']), (TX + 15, T['LSTEP'])], CSTEP, hops=(662,))
wire([(NX1 - 15, yD3), (486, yD3), (486, Pn['LDIR']), (PXx + 15, Pn['LDIR'])], CDIR)
wire([(NX1 - 15, yD2), (462, yD2), (462, Pn['LSTEP']), (PXx + 15, Pn['LSTEP'])], CSTEP, hops=(486,))
badge(590, yD4, 18, CSTEP); badge(520, yD5, 19, CDIR)
badge(560, Pn['LSTEP'], 16, CSTEP); badge(630, Pn['LDIR'], 17, CDIR)


# right-side: power tags, coils, motors
def motor(x, y, name):
    a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='190' height='190' rx='22' fill='url(#mot)'/></g>")
    a(f"<rect x='{x + 10}' y='{y + 10}' width='170' height='170' rx='16' fill='none' stroke='#6b7280' stroke-width='2'/>")
    for dx, dy in ((24, 24), (166, 24), (24, 166), (166, 166)):
        a(f"<circle cx='{x + dx}' cy='{y + dy}' r='8' fill='#111827' stroke='#9ca3af' stroke-width='2'/>")
    a(f"<circle cx='{x + 95}' cy='{y + 95}' r='40' fill='#374151' stroke='#9ca3af' stroke-width='3'/>")
    a(f"<circle cx='{x + 95}' cy='{y + 95}' r='13' fill='url(#alu)'/><rect x='{x + 88}' y='{y + 82}' width='14' height='6' fill='#6b7280'/>")
    t(x + 95, y + 212, name, 16, '#0f172a', 700, 'middle')
    t(x + 95, y + 230, 'NEMA17 stepper', 13, '#475569', 400, 'middle')


for P, x, y0, name, vm, gn, vd in ((T, TX, TY, 'TILT motor', 'W5 12 V bus', 'W7 GND bus', 'W11 5 V bus'),
                                     (Pn, PXx, PYy, 'PAN motor', 'W4 12 V bus', 'W6 GND bus', 'W10 5 V bus')):
    tag(x + 282, P['RVMOT'], vm, C12); tag(x + 282, P['RGND'], gn, CG)
    line([(x + 185, P['RVDD']), (x + 282, P['RVDD'])], C5, 5); tag(x + 282, P['RVDD'], vd, C5)
    t(x + 214, P['RGND2'] + 5, 'empty', 12.5, '#64748b', 700)
    mx, my = 1235, P['R2B'] - 70
    # 4-pin plug
    a(f"<rect x='1110' y='{P['R2B'] - 16}' width='34' height='{P['R1B'] - P['R2B'] + 32}' rx='5' fill='#f8fafc' stroke='#94a3b8' stroke-width='2'/>")
    for k, (pn, col) in enumerate((('2B', CPA), ('2A', CPA), ('1A', CPB), ('1B', CPB))):
        y = P['R' + pn]
        line([(x + 185, y), (1110, y)], col, 5, None if k % 2 == 0 else '12 5')
        line([(1144, y), (mx, y)], col, 5, None if k % 2 == 0 else '12 5')
    # pair brackets
    for (p1, p2, col, lab) in (('2B', '2A', CPA, 'pair A'), ('1A', '1B', CPB, 'pair B')):
        y1, y2 = P['R' + p1], P['R' + p2]
        a(f"<path d='M1160 {y1 - 8} h-6 v{y2 - y1 + 16} h6' fill='none' stroke='{col}' stroke-width='2.5'/>")
        t(1166, (y1 + y2) // 2 + 5, lab, 12.5, col, 700)
    motor(mx, my, name)

# ---- side notes (right of the motors)
NXs = 1470


def note(y, h, title, col, lines_):
    a(f"<rect x='{NXs}' y='{y}' width='486' height='{h}' rx='14' fill='#f8fafc' stroke='{col}' stroke-width='2.2'/>")
    t(NXs + 18, y + 30, title, 17, col, 700)
    for i, s in enumerate(lines_):
        t(NXs + 18, y + 58 + i * 22, s, 14.5, '#1e293b', 400)


note(560, 180, '⚠ Solder bridges (each driver)', '#6b7280', [
    '• MS1 + MS2 + MS3 joined with one blob,',
    '   then ONE wire to 5 V  →  1/16 microstep',
    '• RST + SLP joined with one blob (no wire)',
    '• EN gets ONE wire to GND'])
# magnified bridge picture
bx, by = NXs + 350, 600
for i in range(4):
    a(f"<circle cx='{bx}' cy='{by + i * 26}' r='7' fill='#d6b35a' stroke='#8a6d1f' stroke-width='1.5'/>")
a(f"<rect x='{bx - 12}' y='{by + 14}' width='24' height='78' rx='12' fill='#c0c0c0' stroke='#4b5563' stroke-width='2' opacity='.9'/>")
for i, s in enumerate(('EN', 'MS1', 'MS2', 'MS3')):
    t(bx + 20, by + 5 + i * 26, s, 12.5, '#334155', 700, mono=True)

note(756, 172, '⚡ Capacitor C1 / C2 (100 µF, 25 V+)', '#1e3a8a', [
    'Solder it right at the driver pins:',
    '• long leg (+)  →  VMOT',
    '• striped leg (−)  →  the GND beside VMOT',
    'Backwards = it can burst. Check twice.'])
cx0, cy0 = NXs + 400, 800
a(f"<rect x='{cx0 - 22}' y='{cy0}' width='44' height='70' rx='8' fill='#1e3a8a'/><rect x='{cx0 + 8}' y='{cy0}' width='14' height='70' fill='#cbd5e1'/>")
t(cx0 + 15, cy0 + 40, '−', 16, '#111', 700, 'middle')
line([(cx0 - 10, cy0 + 70), (cx0 - 10, cy0 + 112)], '#9ca3af', 4); line([(cx0 + 12, cy0 + 70), (cx0 + 12, cy0 + 96)], '#9ca3af', 4)
t(cx0 - 26, cy0 + 110, '+', 16, C12, 700, 'middle')

note(944, 180, '🧲 Find the motor coil pairs', CPA, [
    'Multimeter on Ω. Two wires that read',
    '2–4 Ω are ONE coil = one pair.',
    '• pair A → 2B + 2A   • pair B → 1A + 1B',
    'Motor turns the wrong way? Swap the 2 wires',
    'of ONE pair. Never unplug with 12 V ON.'])

note(1140, 222, '🎨 Wire colours in this drawing', '#0b1f3a', [])
leg = [(C12, '12 V (motor power)'), (CG, 'GND (0 V)'), (C5, '5 V (logic)'), (CSTEP, 'STEP signal'),
       (CDIR, 'DIR signal'), (CLAS, 'laser signal'), (CPA, 'motor coil pair A'), (CPB, 'motor coil pair B')]
for i, (col, s) in enumerate(leg):
    xx, yy = NXs + 22 + (i % 2) * 240, 1196 + (i // 2) * 38
    line([(xx, yy), (xx + 44, yy)], col, 6)
    t(xx + 56, yy + 5, s, 14.5, '#1e293b', 400)

# ================================================================ ③ CHECKLIST
CY = 1402
panel(CY, 506, '3', 'Tick every wire', '   Power OFF while wiring. Beep-test 12 V bus ↔ 5 V bus: must be SILENT before power-up.')
rows = [
    (1, 'jack + pin', 'switch MIDDLE leg', C12), (2, 'switch OUT leg', '12 V bus', C12), (3, 'jack − sleeve', 'GND bus', CG),
    (4, '12 V bus', 'PAN VMOT', C12), (5, '12 V bus', 'TILT VMOT', C12), (6, 'PAN GND (by VMOT)', 'GND bus', CG),
    (7, 'TILT GND (by VMOT)', 'GND bus', CG), (8, 'Nano GND', 'GND bus', CG), (9, 'Nano 5V', '5 V bus', C5),
    (10, '5 V bus', 'PAN VDD', C5), (11, '5 V bus', 'TILT VDD', C5), (12, '5 V bus', 'PAN MS1-3 blob', C5),
    (13, '5 V bus', 'TILT MS1-3 blob', C5), (14, 'GND bus', 'PAN EN', CG), (15, 'GND bus', 'TILT EN', CG),
    (16, 'Nano D2', 'PAN STEP', CSTEP), (17, 'Nano D3', 'PAN DIR', CDIR), (18, 'Nano D4', 'TILT STEP', CSTEP),
    (19, 'Nano D5', 'TILT DIR', CDIR), (20, 'Nano D7', 'laser S', CLAS), (21, '5 V bus', 'laser + (middle)', C5),
    (22, 'GND bus', 'laser −', CG)]
extra = [('C1', '100 µF at PAN: + VMOT, − GND', '#1e3a8a'), ('C2', '100 µF at TILT: + VMOT, − GND', '#1e3a8a'),
         ('M', 'each motor: pair A → 2B/2A', CPA), ('M', 'each motor: pair B → 1A/1B', CPB),
         ('B', 'both drivers: MS1-2-3 blob', '#6b7280'), ('B', 'both drivers: RST-SLP blob', '#6b7280')]
allr = [(f'W{n}', f'{f}  →  {to}', c) for n, f, to, c in rows] + [(k, s, c) for k, s, c in extra]
per = 10
for i, (k, s, col) in enumerate(allr):
    cx, cy = 60 + (i // per) * 480, CY + 92 + (i % per) * 38
    a(f"<rect x='{cx}' y='{cy - 15}' width='22' height='22' rx='4' fill='#fff' stroke='#475569' stroke-width='2'/>")
    a(f"<rect x='{cx + 34}' y='{cy - 14}' width='50' height='22' rx='6' fill='{col}'/>")
    t(cx + 59, cy + 2, k, 13, '#fff', 700, 'middle', mono=True)
    t(cx + 96, cy + 2, s, 15, '#0f172a', 400)
# power order box (4th column)
bx0 = 1500
a(f"<rect x='{bx0}' y='{CY + 70}' width='456' height='404' rx='14' fill='#fef2f2' stroke='#dc2626' stroke-width='2.2'/>")
t(bx0 + 20, CY + 104, 'Power ON / OFF order', 19, '#b91c1c', 700)
steps = [('ON', '1. USB into the laptop', '#0284c7'), ('ON', '2. switch 12 V ON', '#16a34a'),
         ('OFF', '1. switch 12 V OFF', '#dc2626'), ('OFF', '2. USB out', '#475569')]
for i, (k, s, col) in enumerate(steps):
    yy = CY + 140 + i * 42
    a(f"<rect x='{bx0 + 20}' y='{yy - 18}' width='52' height='28' rx='6' fill='{col}'/>")
    t(bx0 + 46, yy + 2, k, 13, '#fff', 700, 'middle', mono=True)
    t(bx0 + 86, yy + 3, s, 16, '#0f172a', 700 if i in (1, 2) else 400)
for i, s in enumerate(['Stop with the switch at any heat, smell', 'or grinding sound.',
                       'Set Vref = 0.55 V with USB only, 12 V OFF.', 'Heat sink on every A4988 chip.',
                       'AS5600 sensor: separate sheet, later.']):
    t(bx0 + 20, CY + 336 + i * 24, s, 14.5, '#7f1d1d' if i < 2 else '#1e293b', 700 if i < 2 else 400)

a('</svg>')
svg = '\n'.join(o)
open('wiring_no_breadboard.svg', 'w').write(svg)
open('wiring.html', 'w').write(f"<!doctype html><html><head><meta charset='utf-8'><style>html,body{{margin:0;background:#f1f5f9}}svg{{display:block}}</style></head><body>{svg}</body></html>")
print('ok', len(svg))
