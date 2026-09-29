"""ZeroDrift MK2 on an 830-point breadboard: every part, every wire, numbered.
Drawn from docs/wiring_plan.js (exported to JSON), so the picture cannot disagree with the plan."""
import json, math, sys
Z = json.load(open('/tmp/plan.json'))
C = Z['C']
P = 46                      # hole pitch (px)
BX = 330                    # x of column 1
W, H = 3620, 3220
def cx(c): return BX + (c - 1) * P

# ---- board rows (y)
BY = 900                    # board top edge
yTp = BY + 40; yTm = yTp + P                        # top rails: red (+12 V) outer, blue (GND) inner
ROWY = {}
y = yTm + 1.7 * P
for r in 'abcde': ROWY[r] = y; y += P
y += 0.55 * P
for r in 'fghij': ROWY[r] = y; y += P
yBm = ROWY['j'] + 1.7 * P; yBp = yBm + P            # bottom rails: blue (GND) inner, red (+5 V) outer
BYE = yBp + 40
RAILY = {'T+': yTp, 'T-': yTm, 'B-': yBm, 'B+': yBp}

def pos(end):
    if end[:2] in RAILY and end[2:].isdigit(): return (cx(int(end[2:])), RAILY[end[:2]])
    if end[0] in ROWY and end[1:].isdigit(): return (cx(int(end[1:])), ROWY[end[0]])
    return DEVPIN[end]

SANS = "font-family='Liberation Sans,DejaVu Sans,Arial,sans-serif'"
MONO = "font-family='DejaVu Sans Mono,Liberation Mono,monospace'"
o = []; a = o.append
def t(x, y, s, sz=14, fill='#0f172a', w=400, anc='start', mono=False, extra=''):
    a(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{sz}' font-weight='{w}' fill='{fill}' text-anchor='{anc}' {MONO if mono else SANS} {extra}>{s}</text>")
def rect(x, y, w, h, fill, rx=6, stroke='none', sw=0, extra=''):
    a(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{rx}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}' {extra}/>")

a(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>")
a("""<defs>
<linearGradient id='bb' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#fbfbf8'/><stop offset='1' stop-color='#ecebe4'/></linearGradient>
<linearGradient id='nano' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#1b5bb8'/><stop offset='1' stop-color='#0f3f8a'/></linearGradient>
<linearGradient id='drv' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#c62828'/><stop offset='1' stop-color='#8e1b1b'/></linearGradient>
<linearGradient id='alu' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#eef0f2'/><stop offset='1' stop-color='#9aa2ab'/></linearGradient>
<linearGradient id='cap' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#1e3a8a'/><stop offset='.5' stop-color='#3b5fc8'/><stop offset='1' stop-color='#1e3a8a'/></linearGradient>
<linearGradient id='mot' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#4b5563'/><stop offset='1' stop-color='#1f2937'/></linearGradient>
<linearGradient id='res' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#f3dcb0'/><stop offset='1' stop-color='#caa56a'/></linearGradient>
<radialGradient id='hole' cx='.4' cy='.35' r='.7'><stop offset='0' stop-color='#6b6b6b'/><stop offset='1' stop-color='#1c1c1c'/></radialGradient>
<filter id='sh' x='-20%' y='-20%' width='140%' height='140%'><feDropShadow dx='0' dy='5' stdDeviation='6' flood-color='#0f172a' flood-opacity='.28'/></filter>
<filter id='wsh' x='-5%' y='-5%' width='110%' height='110%'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-color='#000' flood-opacity='.35'/></filter>
<pattern id='grid' width='26' height='26' patternUnits='userSpaceOnUse'><path d='M26 0H0V26' fill='none' stroke='#e2e8f0' stroke-width='1'/></pattern>
</defs>""")
a(f"<rect width='{W}' height='{H}' fill='#f1f5f9'/><rect width='{W}' height='{H}' fill='url(#grid)'/>")

# ---- header
rect(0, 0, W, 120, '#0b1f3a', 0)
t(46, 56, 'ZeroDrift MK2 · full breadboard wiring (830-point board)', 40, '#fff', 700)
t(46, 96, f"{len(Z['wires'])} numbered wires · every hole named (column 1–63, row a–j) · pins match rig_firmware_v2.ino · wire with EVERYTHING unplugged", 20, '#bcd3ee')
t(W - 46, 60, 'pan D2/D3 · tilt D4/D5 · laser D7 · vibration D8', 20, '#7dd3fc', 700, 'end', True)
t(W - 46, 94, 'I²C: A4 = SDA · A5 = SCL · multiplexer 0x70', 20, '#7dd3fc', 400, 'end', True)

# ================= BREADBOARD =================
a(f"<g filter='url(#sh)'><rect x='{cx(1)-1.6*P}' y='{BY}' width='{cx(63)-cx(1)+3.2*P}' height='{BYE-BY}' rx='18' fill='url(#bb)' stroke='#cfcdc3' stroke-width='2'/></g>")
# middle channel
mid = (ROWY['e'] + ROWY['f']) / 2
rect(cx(1) - 1.2 * P, mid - 0.16 * P, cx(63) - cx(1) + 2.4 * P, 0.32 * P, '#d9d6cb', 4)
# rail stripes
for ry, col in ((yTp - 0.62 * P, '#e53935'), (yTm + 0.62 * P, '#1e4fd8'), (yBm - 0.62 * P, '#1e4fd8'), (yBp + 0.62 * P, '#e53935')):
    rect(cx(1) - 1.0 * P, ry - 2, cx(63) - cx(1) + 2.0 * P, 4, col, 2)
for ry, lab, col in ((yTp, '+', '#e53935'), (yTm, '−', '#1e4fd8'), (yBm, '−', '#1e4fd8'), (yBp, '+', '#e53935')):
    t(cx(1) - 1.25 * P, ry + 7, lab, 22, col, 700, 'middle'); t(cx(63) + 1.25 * P, ry + 7, lab, 22, col, 700, 'middle')
# rail names
t(cx(1) - 1.65 * P, yTp + 6, '12 V', 16, '#e53935', 700, 'end'); t(cx(1) - 1.65 * P, yTm + 6, 'GND', 16, '#1e4fd8', 700, 'end')
t(cx(1) - 1.65 * P, yBm + 6, 'GND', 16, '#1e4fd8', 700, 'end'); t(cx(1) - 1.65 * P, yBp + 6, '5 V', 16, '#b45309', 700, 'end')
# holes
for rname, ry in RAILY.items():
    for c in Z['RAIL_COLS']:
        a(f"<rect x='{cx(c)-6}' y='{ry-6}' width='12' height='12' rx='2' fill='url(#hole)'/>")
for r, ry in ROWY.items():
    for c in range(1, 64):
        a(f"<rect x='{cx(c)-6}' y='{ry-6}' width='12' height='12' rx='2' fill='url(#hole)'/>")
    t(cx(1) - 0.9 * P, ry + 6, r, 17, '#6b6b6b', 700, 'middle', True); t(cx(63) + 0.9 * P, ry + 6, r, 17, '#6b6b6b', 700, 'middle', True)
for c in range(1, 64):
    if c == 1 or c % 5 == 0:
        t(cx(c), ROWY['a'] - 0.62 * P, str(c), 15, '#6b6b6b', 700, 'middle', True)
        t(cx(c), ROWY['j'] + 0.8 * P, str(c), 15, '#6b6b6b', 700, 'middle', True)

# ================= OFF-BOARD DEVICES =================
DEVPIN = {}
def pinrow(dev, names, x0, y0, dx, lab_below=True, colr='#d6b35a', txt='#fff', size=14):
    for i, n in enumerate(names):
        x = x0 + i * dx
        a(f"<circle cx='{x}' cy='{y0}' r='8' fill='{colr}' stroke='#7a5f16' stroke-width='2'/>")
        t(x, y0 + (26 if lab_below else -16), n, size, txt, 700, 'middle', True)
        DEVPIN[f'{dev}:{n}'] = (x, y0)

def board(x, y, w, h, fill, title, sub, tcol='#fff'):
    a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='{fill}'/></g>")
    t(x + w / 2, y - 30, title, 21, '#0f172a', 700, 'middle'); t(x + w / 2, y - 9, sub, 15, '#475569', 400, 'middle')

# -- laser (top-left, above cols 5-11)
lx, ly = cx(4), 610
board(lx, ly, 6 * P, 92, '#18181b', 'LASER  KY-008', 'on the tilt head')
rect(lx + 6 * P, ly + 30, 60, 34, 'url(#alu)', 6); a(f"<circle cx='{lx+6*P+64}' cy='{ly+47}' r='9' fill='#ef4444'/>")
pinrow('las', ['S', 'mid', '-'], lx + 0.9 * P, ly + 66, 2.1 * P, False)
t(lx + 0.9 * P + 2.1 * P, ly + 88, 'no wire', 12, '#94a3b8', 700, 'middle')

# -- pan / tilt motors (above their drivers)
def motor(dev, x, y, name, sub):
    a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='190' height='190' rx='22' fill='url(#mot)'/></g>")
    for dx, dy in ((24, 24), (166, 24), (24, 166), (166, 166)): a(f"<circle cx='{x+dx}' cy='{y+dy}' r='8' fill='#111827' stroke='#9ca3af' stroke-width='2'/>")
    a(f"<circle cx='{x+95}' cy='{y+95}' r='40' fill='#374151' stroke='#9ca3af' stroke-width='3'/><circle cx='{x+95}' cy='{y+95}' r='13' fill='url(#alu)'/>")
    t(x + 95, y - 34, name, 21, '#0f172a', 700, 'middle'); t(x + 95, y - 12, sub, 15, '#475569', 400, 'middle')
    # connector + 4 wire tails at bottom
    rect(x + 45, y + 190, 100, 22, '#f8fafc', 4, '#94a3b8', 2)
    for i, (pin, colr) in enumerate((('A1', C['mBlack']), ('A2', C['mGreen']), ('B1', C['mRed']), ('B2', C['mBlue']))):
        px = x + 58 + i * 25
        DEVPIN[f'{dev}:{pin}'] = (px, y + 214)
motor('pm', cx(29) + 0.5 * P - 95, 470, 'PAN MOTOR', 'NEMA17 · bottom')
motor('tm', cx(41) + 0.5 * P - 95, 470, 'TILT MOTOR', 'NEMA17 · in the head')

# -- power: adapter -> jack -> switch (above cols 50-63)
sx, sy = cx(52) - 60, 650
a(f"<g filter='url(#sh)'><rect x='{sx}' y='{sy}' width='130' height='80' rx='12' fill='#334155'/></g>")
a(f"<rect x='{sx+56}' y='{sy-38}' width='20' height='44' rx='8' fill='#cbd5e1' stroke='#64748b' stroke-width='2' transform='rotate(18 {sx+66} {sy})'/>")
t(sx + 65, sy + 30, 'KILL', 15, '#f1f5f9', 700, 'middle'); t(sx + 65, sy + 50, 'SWITCH', 15, '#f1f5f9', 700, 'middle')
t(sx + 65, sy - 52, 'TOGGLE SWITCH', 21, '#0f172a', 700, 'middle')
pinrow('sw', ['OUT', 'MID', 'spare'], sx + 25, sy + 96, 40, True, '#cbd5e1', '#334155', 12)
jx, jy = cx(58) - 20, 640
a(f"<g filter='url(#sh)'><rect x='{jx}' y='{jy}' width='130' height='100' rx='12' fill='#27272a'/></g>")
a(f"<circle cx='{jx+65}' cy='{jy+42}' r='24' fill='#0a0a0a' stroke='#52525b' stroke-width='4'/><circle cx='{jx+65}' cy='{jy+42}' r='6' fill='#d4d4d8'/>")
t(jx + 65, jy + 88, 'DC JACK', 14, '#e4e4e7', 700, 'middle')
t(jx + 65, jy - 42, 'DC JACK', 21, '#0f172a', 700, 'middle'); t(jx + 65, jy - 20, '3 legs: + pin · − sleeve · empty', 15, '#475569', 400, 'middle')
pinrow('jack', ['+', '-', 'x'], jx + 25, jy + 116, 40, True, '#cbd5e1', '#334155', 13)
ax, ay = jx + 190, jy + 5
a(f"<g filter='url(#sh)'><rect x='{ax}' y='{ay}' width='150' height='90' rx='12' fill='#1f2937'/></g>")
t(ax + 75, ay + 40, '12 V · 2 A', 18, '#fff', 700, 'middle'); t(ax + 75, ay + 64, 'adapter', 14, '#cbd5e1', 400, 'middle')
a(f"<path d='M{ax} {ay+45} C {ax-40} {ay+45}, {jx+150} {jy+42}, {jx+100} {jy+42}' fill='none' stroke='#111' stroke-width='9' stroke-linecap='round'/>")
t(ax + 75, ay - 16, 'plug into the wall LAST', 15, '#b91c1c', 700, 'middle')
# jack + to switch MID is an off-board wire (drawn with the other wires)

# -- multiplexer (below cols 7-21)
mx, my = cx(3), BYE + 250
board(mx, my, 15 * P, 120, '#1e3a8a', 'MULTIPLEXER  TCA9548A', 'stays OFF the breadboard · male-female jumpers')
pinrow('mux', ['VIN', 'GND', 'SDA', 'SCL', 'RST', 'A0', 'A1', 'A2'], mx + 0.9 * P, my + 26, 1.72 * P, True, '#d6b35a', '#fff', 13)
pinrow('mux', ['SD0', 'SC0'], mx + 11.4 * P, my + 96, 1.7 * P, False, '#d6b35a', '#fff', 13)
t(mx + 0.9 * P + 4 * 1.72 * P, my + 76, 'no wire', 12, '#93c5fd', 700, 'middle')
t(mx + 5.5 * P, my + 102, 'channel 0 → AS5600', 14, '#bfdbfe', 400, 'middle')

# -- AS5600 (below cols 46-53)
sx5, sy5 = cx(44), BYE + 250
board(sx5, sy5, 8.5 * P, 120, '#6d28d9', 'AS5600 ANGLE SENSOR', 'on the rig, under the pan shaft magnet')
pinrow('as', ['SDA', 'SCL', 'VCC', 'GND', 'DIR'], sx5 + 0.8 * P, sy5 + 26, 1.72 * P, True, '#d6b35a', '#fff', 13)
a(f"<circle cx='{sx5+4.25*P}' cy='{sy5+88}' r='14' fill='#111827'/>")

# -- vibration motor (below cols 56-61)
vx, vy = cx(22) + 10, BYE + 430
t(vx + 60, vy + 130, 'VIBRATION MOTOR', 21, '#0f172a', 700, 'middle'); t(vx + 60, vy + 152, 'small 3-5 V coin / pager motor · on the rig base', 15, '#475569', 400, 'middle')
a(f"<g filter='url(#sh)'><circle cx='{vx+60}' cy='{vy+52}' r='46' fill='url(#alu)' stroke='#6b7280' stroke-width='3'/></g>")
a(f"<circle cx='{vx+60}' cy='{vy+52}' r='30' fill='none' stroke='#9ca3af' stroke-width='2'/><path d='M{vx+42} {vy+52} a18 18 0 0 1 36 0' fill='#f97316' opacity='.85'/>")
t(vx + 60, vy + 58, 'M', 22, '#374151', 700, 'middle')
DEVPIN['vm:+'] = (vx + 42, vy + 8); DEVPIN['vm:-'] = (vx + 78, vy + 8)
t(vx + 30, vy + 22, 'red +', 14, C['mRed'], 700, 'end'); t(vx + 92, vy + 22, 'blue −', 14, C['mBlue'], 700)

# -- laptop (bottom-left) + USB
lpx, lpy = cx(1) - 1.5 * P, BYE + 560
a(f"<g filter='url(#sh)'><rect x='{lpx}' y='{lpy}' width='230' height='140' rx='10' fill='#1f2937'/></g>")
rect(lpx + 12, lpy + 12, 206, 116, '#0b1a30', 6); t(lpx + 115, lpy + 64, 'LAPTOP', 20, '#7dd3fc', 700, 'middle'); t(lpx + 115, lpy + 92, 'Chrome · live page', 14, '#94a3b8', 400, 'middle')
a(f"<path d='M{lpx-14} {lpy+140} h258 l-18 22 h-222 z' fill='#374151'/>")
DEVPIN['laptop:USB'] = (lpx + 230, lpy + 70)

# ================= ON-BOARD PARTS =================
def pinlab(x, y, s, col='#fff', up=True, sz=12):
    t(x, y + (-14 if up else 22), s, sz, col, 700, 'middle', True)
def module(key, fill, title):
    Pp = Z['parts'][key]; c0, c1 = Pp['cols']; r0, r1 = Pp['rows']
    x0 = cx(c0) - 0.45 * P; x1 = cx(c1) + 0.45 * P; y0 = ROWY[r0] - 0.42 * P; y1 = ROWY[r1] + 0.42 * P
    a(f"<g filter='url(#sh)'><rect x='{x0}' y='{y0}' width='{x1-x0}' height='{y1-y0}' rx='8' fill='{fill}'/></g>")
    for i, n in enumerate(Pp['top']):
        c = cx(c0 + i); a(f"<rect x='{c-8}' y='{ROWY[r0]-8}' width='16' height='16' rx='3' fill='#d6b35a' stroke='#7a5f16' stroke-width='1.5'/>")
        pinlab(c, ROWY[r0] + 32, n, '#fff', True, 11.5)
    for i, n in enumerate(Pp['bottom']):
        c = cx(c0 + i); a(f"<rect x='{c-8}' y='{ROWY[r1]-8}' width='16' height='16' rx='3' fill='#d6b35a' stroke='#7a5f16' stroke-width='1.5'/>")
        pinlab(c, ROWY[r1] - 32, n, '#fff', False, 11.5)
    return x0, y0, x1, y1
x0, y0, x1, y1 = module('nano', 'url(#nano)', 'NANO')
t((x0 + x1) / 2, (y0 + y1) / 2 + 8, 'ARDUINO  NANO', 24, '#dbeafe', 700, 'middle')
rect(x0 - 34, (y0 + y1) / 2 - 26, 44, 52, 'url(#alu)', 6, '#6b7280', 2)
t(x0 - 12, (y0 + y1) / 2 + 48, 'USB-C', 13, '#1e3a8a', 700, 'middle')
DEVPIN['usb:NANO'] = (x0 - 34, (y0 + y1) / 2)
for key, name in (('pan', 'PAN DRIVER'), ('tilt', 'TILT DRIVER')):
    x0, y0, x1, y1 = module(key, 'url(#drv)', name)
    xm = (x0 + x1) / 2; ym = (y0 + y1) / 2
    rect(xm - 44, ym - 30, 60, 60, 'url(#alu)', 4, '#6b7280', 1.5)
    for k in range(5): rect(xm - 40 + k * 11.5, ym - 26, 5, 52, '#9ca3af', 1)
    a(f"<circle cx='{xm+40}' cy='{ym}' r='13' fill='#e5e7eb' stroke='#6b7280' stroke-width='2'/><path d='M{xm+33} {ym}h14M{xm+40} {ym-7}v14' stroke='#374151' stroke-width='3'/>")
    t(xm, y0 - 10, name + '  A4988', 17, '#7f1d1d', 700, 'middle')

# capacitors on the top rails
for cp in Z['caps']:
    c = cx(cp['col']); yy = (yTp + yTm) / 2
    a(f"<line x1='{c-7}' y1='{yTp}' x2='{c-7}' y2='{yy-26}' stroke='#9ca3af' stroke-width='3'/><line x1='{c+7}' y1='{yTm}' x2='{c+7}' y2='{yy+2}' stroke='#9ca3af' stroke-width='3'/>")
    a(f"<g filter='url(#sh)'><rect x='{c-22}' y='{yy-110}' width='44' height='84' rx='10' fill='url(#cap)'/></g>")
    rect(c + 6, yy - 110, 14, 84, '#cbd5e1', 3); t(c + 13, yy - 62, '−', 16, '#111', 700, 'middle')
    t(c - 2, yy - 124, cp['id'] + ' 100 µF', 16, '#1e3a8a', 700, 'middle')
    t(c - 34, yy - 60, '+', 18, '#e53935', 700, 'middle')

# vibration driver parts (Q1, R1, D1)
V = Z['vib']
def hp(h): return pos(h)
(qe, qy), (qb, _), (qc, _) = hp(V['q']['E']), hp(V['q']['B']), hp(V['q']['C'])
for xx in (qe, qb, qc): a(f"<line x1='{xx}' y1='{qy}' x2='{xx}' y2='{qy-26}' stroke='#9ca3af' stroke-width='3'/>")
a(f"<g filter='url(#sh)'><path d='M{qe-16} {qy-22} L{qc+16} {qy-22} L{qc+16} {qy-48} A {(qc-qe)/2+16} 26 0 0 0 {qe-16} {qy-48} Z' fill='#1f2937'/></g>")
t((qe + qc) / 2, qy - 60, 'Q1', 17, '#e5e7eb', 700, 'middle')
(rx, ry0), (_, ry1) = hp(V['r'][0]), hp(V['r'][1])
a(f"<line x1='{rx}' y1='{ry0}' x2='{rx}' y2='{ry1}' stroke='#9ca3af' stroke-width='3'/>")
a(f"<g filter='url(#sh)'><rect x='{rx-12}' y='{(ry0+ry1)/2-30}' width='24' height='60' rx='11' fill='url(#res)'/></g>")
for k, bc in enumerate(('#7c4a1e', '#111', '#dc2626', '#d4af37')): rect(rx - 12, (ry0 + ry1) / 2 - 22 + k * 11 + (6 if k == 3 else 0), 24, 5, bc, 1)
t(rx + 22, (ry0 + ry1) / 2 + 5, 'R1 1 kΩ', 15, '#0f172a', 700)
(dax, dy_), (dkx, _) = hp(V['d']['A']), hp(V['d']['K'])
a(f"<line x1='{dax}' y1='{dy_}' x2='{dkx}' y2='{dy_}' stroke='#9ca3af' stroke-width='3'/>")
a(f"<g filter='url(#sh)'><rect x='{(dax+dkx)/2-28}' y='{dy_-10}' width='56' height='20' rx='9' fill='#f59e0b' opacity='.92'/></g>")
rect((dax + dkx) / 2 + 14, dy_ - 10, 9, 20, '#111', 1)
t((dax + dkx) / 2, dy_ - 16, 'D1 1N4148', 13, '#0f172a', 700, 'middle')

# ================= WIRES =================
lbls = []
LANE = lambda k: yTm + 24 + k * 13
def ortho(pts, r=10):
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for (xa, ya), (xb, yb), (xc, yc) in zip(pts, pts[1:], pts[2:]):
        ux, uy = (xb - xa), (yb - ya); L1 = math.hypot(ux, uy) or 1
        vx, vy = (xc - xb), (yc - yb); L2 = math.hypot(vx, vy) or 1
        rr = min(r, L1 / 2, L2 / 2)
        d += f" L{xb-ux/L1*rr:.1f} {yb-uy/L1*rr:.1f} Q{xb:.1f} {yb:.1f} {xb+vx/L2*rr:.1f} {yb+vy/L2*rr:.1f}"
    d += f" L{pts[-1][0]:.1f} {pts[-1][1]:.1f}"
    return d
def via(lane, xdown, ytarget=None):
    return lambda x1, y1, x2, y2: ortho([(x1, y1), (x1, LANE(lane)), (xdown, LANE(lane)), (xdown, ytarget if ytarget else y2), (x2, y2)])
ROUTE = {
    28: via(0, cx(48.6)), 27: via(1, cx(48.0)), 25: via(2, cx(36.6)), 26: via(3, cx(36.0)),
    51: lambda x1, y1, x2, y2: ortho([(x1, y1), (x1, LANE(4)), (x2, LANE(4)), (x2, y2)]),
    9: lambda x1, y1, x2, y2: ortho([(x1, y1), (x2, y1), (x2, y2)]),
    18: lambda x1, y1, x2, y2: ortho([(x1, y1), (x2, y1), (x2, y2)]),
}
def wire(w):
    (x1, y1), (x2, y2) = pos(w['from']), pos(w['to'])
    col = w['color']; n = w['n']
    fp, tp = Z['wires'], None
    rail = lambda e: e[:2] in RAILY and e[2:].isdigit()
    if n in ROUTE:
        d = ROUTE[n](x1, y1, x2, y2); lx = ly = 0
    elif abs(x1 - x2) < 1 and (rail(w['from']) or rail(w['to'])) and abs(y1 - y2) < 4 * P:
        d = f'M{x1} {y1} L{x2} {y2}'; lx, ly = x1 + 0, (y1 + y2) / 2
    else:
        dy = max(60, abs(y2 - y1) * 0.45)
        s1 = -1 if y1 > y2 else 1
        # bulge wires that stay inside the board so they arch above it
        if w['from'][0] in ROWY and w['to'][0] in ROWY and w['from'][1:].isdigit() and w['to'][1:].isdigit():
            d = f'M{x1} {y1} C {x1} {y1-90}, {x2} {y2-90-abs(x2-x1)*0.08}, {x2} {y2}'
        else:
            d = f'M{x1} {y1} C {x1} {y1+s1*dy}, {x2} {y2-s1*dy}, {x2} {y2}'
        lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
    a(f"<path d='{d}' fill='none' stroke='#ffffff' stroke-width='10' stroke-linecap='round' opacity='.9'/>")
    a(f"<path d='{d}' fill='none' stroke='{col}' stroke-width='6' stroke-linecap='round' filter='url(#wsh)'/>")
    for (x, y) in ((x1, y1), (x2, y2)):
        a(f"<rect x='{x-5}' y='{y-5}' width='10' height='10' rx='2' fill='#c0c0c0' stroke='#555' stroke-width='1'/>")
    return d
BADGE = {}
paths = {}
for w in Z['wires']: paths[w['n']] = wire(w)

# badge positions: along each path at 50% (computed in the browser afterwards), stored as data
a("<g id='badges'></g>")
a(f"<script type='application/json' id='wmeta'>{json.dumps([[w['n'], w['color']] for w in Z['wires']])}</script>")

# ================= LEGEND / CHECKLIST =================
LY = 2300
rect(40, LY, W - 80, H - LY - 30, '#ffffff', 22, '#cbd5e1', 2)
t(80, LY + 50, 'Tick every wire', 28, '#0b1f3a', 700)
t(330, LY + 50, 'go in order: power → drivers → STEP/DIR → motors → sensor → laser → vibration → USB', 18, '#475569')
rows = Z['wires']; per = 19
for i, w in enumerate(rows):
    x = 70 + (i // per) * 880; y = LY + 96 + (i % per) * 39
    a(f"<rect x='{x}' y='{y-17}' width='22' height='22' rx='4' fill='#fff' stroke='#475569' stroke-width='2'/>")
    a(f"<circle cx='{x+50}' cy='{y-6}' r='15' fill='{w['color']}' stroke='#fff' stroke-width='2'/>")
    t(x + 50, y - 1, str(w['n']), 14, '#fff', 700, 'middle')
    def code(e):
        if ':' in e: return ''
        return f" [col {e[2:]}]" if e[:2] in RAILY else f" [{e}]"
    fa = w['a'].replace('  ', ' ') + code(w['from'])
    fb = w['b'].replace('  ', ' ') + code(w['to'])
    t(x + 76, y, f"{fa} → {fb}", 15, '#0f172a')
# extras column (parts that are not wires)
ex = 70 + 3 * 880; ey = LY + 96
t(ex, ey - 6, 'Also on the board', 20, '#0b1f3a', 700)
extras = [('C1', '100 µF at col 25: long leg T+ (red), stripe T− (blue)'), ('C2', '100 µF at col 37: same way round'),
          ('J', 'pan: short jumper j31 ↔ j32 (RST–SLP)'), ('J', 'tilt: short jumper j43 ↔ j44'),
          ('R1', '1 kΩ, e20 ↔ f20 across the gap (brown-black-red)'), ('Q1', '2N2222 legs in j19 j20 j21, flat face toward you (E B C)'),
          ('D1', '1N4148, f21 ↔ f24, black stripe at f24'), ('V', 'Vref 0.55 V on both drivers (12 V OFF)')]
for i, (k, s) in enumerate(extras):
    y = ey + 36 + i * 39
    a(f"<rect x='{ex}' y='{y-17}' width='22' height='22' rx='4' fill='#fff' stroke='#475569' stroke-width='2'/>")
    rect(ex + 32, y - 20, 42, 28, '#0b1f3a', 6); t(ex + 53, y, k, 14, '#fff', 700, 'middle')
    t(ex + 84, y, s, 15, '#0f172a')
yy = ey + 36 + len(extras) * 39 + 20
rect(ex, yy, 560, 250, '#fef2f2', 14, '#dc2626', 2)
for i, (s, b) in enumerate([('Rails: follow the RED / BLUE line printed', 1), ('next to each rail row on YOUR board.', 0),
                            ('Beep-test: TOP red ↔ BOTTOM red = SILENT.', 1), ('12 V must never reach 5 V, the Nano or VDD.', 0),
                            ('Power ON: USB, then 12 V switch.', 1), ('Power OFF: 12 V switch, then USB.', 0)]):
    t(ex + 20, yy + 40 + i * 36, s, 17, '#7f1d1d' if b else '#1e293b', 700 if b else 400)

a('</svg>')
svg = '\n'.join(o)
open('bb.svg', 'w').write(svg)
# badges are placed in the browser along each path, then the page is screenshot
html = f"""<!doctype html><html><head><meta charset='utf-8'><style>html,body{{margin:0;background:#f1f5f9}}svg{{display:block}}</style></head><body>{svg}
<script>
const svg=document.querySelector('svg'),NS='http://www.w3.org/2000/svg',meta=JSON.parse(document.getElementById('wmeta').textContent);
const paths=[...svg.querySelectorAll('path[stroke-width="6"]')], g=document.getElementById('badges'), placed=[];
paths.forEach((p,i)=>{{ const [n,col]=meta[i]; const L=p.getTotalLength(); let best=null;
  for(const f of [.5,.42,.58,.34,.66,.26,.74,.2,.8]){{ const q=p.getPointAtLength(L*f); if(placed.every(o=>Math.hypot(o.x-q.x,o.y-q.y)>34)){{best=q;break}} }}
  if(!best) best=p.getPointAtLength(L*.5); placed.push(best);
  const c=document.createElementNS(NS,'circle'); c.setAttribute('cx',best.x); c.setAttribute('cy',best.y); c.setAttribute('r',15); c.setAttribute('fill',col); c.setAttribute('stroke','#fff'); c.setAttribute('stroke-width',3); g.appendChild(c);
  const t=document.createElementNS(NS,'text'); t.setAttribute('x',best.x); t.setAttribute('y',best.y+5); t.setAttribute('text-anchor','middle'); t.setAttribute('font-size',14); t.setAttribute('font-weight',700); t.setAttribute('fill','#fff'); t.setAttribute('font-family','Liberation Sans,Arial'); t.textContent=n; g.appendChild(t); }});
document.body.dataset.ready=1;
</script></body></html>"""
open('bb.html', 'w').write(html)
print('ok', len(Z['wires']))
