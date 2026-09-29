"""Vibration motor sheet: (1) breadboard close-up, (2) circuit, (3) where it is fixed on the rig."""
import json, math
Z = json.load(open('/tmp/plan.json')); C = Z['C']
W, H = 3000, 2420
o = []; a = o.append
SANS = "font-family='Liberation Sans,DejaVu Sans,Arial,sans-serif'"; MONO = "font-family='DejaVu Sans Mono,Liberation Mono,monospace'"
def t(x, y, s, sz=16, fill='#0f172a', w=400, anc='start', mono=False, extra=''):
    a(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{sz}' font-weight='{w}' fill='{fill}' text-anchor='{anc}' {MONO if mono else SANS} {extra}>{s}</text>")
def rect(x, y, w, h, fill, rx=6, stroke='none', sw=0): a(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{rx}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")
def line(pts, col, wd=6):
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    a(f"<path d='{d}' fill='none' stroke='#fff' stroke-width='{wd+5}' stroke-linecap='round' stroke-linejoin='round'/><path d='{d}' fill='none' stroke='{col}' stroke-width='{wd}' stroke-linecap='round' stroke-linejoin='round'/>")
def badge(x, y, n, col, r=17): a(f"<circle cx='{x}' cy='{y}' r='{r}' fill='{col}' stroke='#fff' stroke-width='3'/>"); t(x, y + 6, str(n), 16, '#fff', 700, 'middle')
def panel(x, y, w, h, num, title):
    rect(x, y, w, h, '#fff', 22, '#cbd5e1', 2); rect(x, y, 60, 52, '#0b1f3a', 14); t(x + 30, y + 36, num, 26, '#fff', 700, 'middle'); t(x + 78, y + 36, title, 26, '#0b1f3a', 700)
a(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>")
a("""<defs><pattern id='grid' width='26' height='26' patternUnits='userSpaceOnUse'><path d='M26 0H0V26' fill='none' stroke='#e2e8f0' stroke-width='1'/></pattern>
<linearGradient id='bb' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#fbfbf8'/><stop offset='1' stop-color='#ecebe4'/></linearGradient>
<linearGradient id='alu' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#eef0f2'/><stop offset='1' stop-color='#9aa2ab'/></linearGradient>
<linearGradient id='res' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#f3dcb0'/><stop offset='1' stop-color='#caa56a'/></linearGradient>
<linearGradient id='mot' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#4b5563'/><stop offset='1' stop-color='#1f2937'/></linearGradient>
<linearGradient id='wood' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#d9b98a'/><stop offset='1' stop-color='#b8935f'/></linearGradient>
<radialGradient id='hole' cx='.4' cy='.35' r='.7'><stop offset='0' stop-color='#6b6b6b'/><stop offset='1' stop-color='#1c1c1c'/></radialGradient>
<filter id='sh' x='-20%' y='-20%' width='140%' height='140%'><feDropShadow dx='0' dy='5' stdDeviation='6' flood-color='#0f172a' flood-opacity='.28'/></filter>
<filter id='wsh' x='-5%' y='-5%' width='110%' height='110%'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-color='#000' flood-opacity='.35'/></filter></defs>""")
a(f"<rect width='{W}' height='{H}' fill='#f1f5f9'/><rect width='{W}' height='{H}' fill='url(#grid)'/>")
rect(0, 0, W, 110, '#0b1f3a', 0)
t(46, 54, 'ZeroDrift MK2 · vibration motor', 38, '#fff', 700)
t(46, 90, 'the “platform shake” demo: serial  V1 = shake ON · V0 = OFF · Arduino pin D8 drives it through a transistor, never straight from the pin', 19, '#bcd3ee')

# ============ 1: BREADBOARD CLOSE-UP (columns 15-27, rows a-j) ============
panel(40, 140, 1500, 1290, '1', 'On the breadboard: columns 15 – 27')
P = 78; c0 = 15; X0 = 150; Y0 = 330
cx = lambda c: X0 + (c - c0) * P
rows = 'abcdefghij'; ry = {}
y = Y0
for r in 'abcde': ry[r] = y; y += P
y += 34
for r in 'fghij': ry[r] = y; y += P
yG = ry['j'] + 110; y5 = yG + P
rect(cx(c0) - 60, Y0 - 78, cx(27) - cx(c0) + 120, y5 - Y0 + 160, 'url(#bb)', 16, '#cfcdc3', 2)
rect(cx(c0) - 50, (ry['e'] + ry['f']) / 2 - 12, cx(27) - cx(c0) + 100, 24, '#d9d6cb', 4)
rect(cx(c0) - 50, yG - 44, cx(27) - cx(c0) + 100, 5, '#1e4fd8', 2); rect(cx(c0) - 50, y5 + 44, cx(27) - cx(c0) + 100, 5, '#e53935', 2)
t(cx(c0) - 58, yG + 8, 'GND', 17, '#1e4fd8', 700, 'end'); t(cx(c0) - 58, y5 + 8, '+5 V', 17, '#b45309', 700, 'end')
RAILC = Z['RAIL_COLS']
for c in range(c0, 28):
    t(cx(c), Y0 - 34, str(c), 17, '#6b6b6b', 700, 'middle', True)
    for r in rows: a(f"<rect x='{cx(c)-9}' y='{ry[r]-9}' width='18' height='18' rx='3' fill='url(#hole)'/>")
    if c in RAILC:
        for yy in (yG, y5): a(f"<rect x='{cx(c)-9}' y='{yy-9}' width='18' height='18' rx='3' fill='url(#hole)'/>")
for r in rows: t(cx(c0) - 74, ry[r] + 6, r, 18, '#6b6b6b', 700, 'middle', True); t(cx(27) + 74, ry[r] + 6, r, 18, '#6b6b6b', 700, 'middle', True)
# strips highlight (which holes are joined)
def strip(c, top, col):
    rr = 'abcde' if top else 'fghij'; a(f"<rect x='{cx(c)-16}' y='{ry[rr[0]]-16}' width='32' height='{ry[rr[-1]]-ry[rr[0]]+32}' rx='14' fill='{col}' opacity='.16'/>")
strip(20, True, '#f97316'); strip(20, False, '#f97316'); strip(19, False, '#111827'); strip(21, False, '#2563eb'); strip(24, False, '#dc2626')
def hp(h): return (cx(int(h[1:])), ry[h[0]])
V = Z['vib']
# nano pin D8 arrives at c8 (off to the left)
line([(70, ry['b']), (cx(20), ry['b'])], C['vib'], 8)
t(110, 232, 'orange wire 51 comes from the Nano: pin D8 = hole c8', 18, '#c2410c', 700)
badge(cx(17.5), ry['b'], 51, C['vib'])
# resistor across the gap e20 - f20
rx, r0 = hp(V['r'][0]); _, r1 = hp(V['r'][1])
a(f"<line x1='{rx}' y1='{r0}' x2='{rx}' y2='{r1}' stroke='#9ca3af' stroke-width='5'/><g filter='url(#sh)'><rect x='{rx-16}' y='{(r0+r1)/2-40}' width='32' height='80' rx='14' fill='url(#res)'/></g>")
for k, bc in enumerate(('#7c4a1e', '#111', '#dc2626', '#d4af37')): rect(rx - 16, (r0 + r1) / 2 - 30 + k * 15 + (8 if k == 3 else 0), 32, 7, bc, 1)
t(rx + 30, (r0 + r1) / 2 + 6, 'R1  1 kΩ', 20, '#0f172a', 700); t(rx + 30, (r0 + r1) / 2 + 30, 'brown-black-red', 14, '#475569')
# transistor legs j19 j20 j21, body up
qs = [hp(V['q'][k]) for k in 'EBC']
for (xx, yy), lab in zip(qs, ('E', 'B', 'C')):
    a(f"<line x1='{xx}' y1='{yy}' x2='{xx}' y2='{yy-46}' stroke='#9ca3af' stroke-width='5'/>")
a(f"<g filter='url(#sh)'><path d='M{qs[0][0]-30} {qs[0][1]-44} L{qs[2][0]+30} {qs[0][1]-44} L{qs[2][0]+30} {qs[0][1]-92} A {(qs[2][0]-qs[0][0])/2+30} 52 0 0 0 {qs[0][0]-30} {qs[0][1]-92} Z' fill='#1f2937'/></g>")
t((qs[0][0] + qs[2][0]) / 2, qs[0][1] - 62, '2N2222', 17, '#e5e7eb', 700, 'middle', True)
for (xx, yy), lab in zip(qs, ('E', 'B', 'C')):
    a(f"<circle cx='{xx}' cy='{yy+38}' r='18' fill='#fff' stroke='#0f172a' stroke-width='2'/>"); t(xx, yy + 45, lab, 20, '#0f172a', 700, 'middle')
t(qs[2][0] + 36, qs[2][1] + 45, 'Q1 · flat face toward you', 17, '#0f172a', 700)
# diode f21-f24
d0 = hp(V['d']['A']); d1 = hp(V['d']['K'])
a(f"<line x1='{d0[0]}' y1='{d0[1]}' x2='{d1[0]}' y2='{d1[1]}' stroke='#9ca3af' stroke-width='5'/><g filter='url(#sh)'><rect x='{(d0[0]+d1[0])/2-46}' y='{d0[1]-15}' width='92' height='30' rx='13' fill='#f59e0b'/></g>")
rect((d0[0] + d1[0]) / 2 + 24, d0[1] - 15, 14, 30, '#111', 2)
t((d0[0] + d1[0]) / 2 + 40, d0[1] - 50, 'D1  1N4148  (stripe at 24)', 17, '#0f172a', 700, 'middle'); # wire 52: g19 -> GND rail col 19? (rail holes: 15-17 are a group... use column 19 hole if exists)
def railhole(c, yy): return (cx(c), yy)
line([hp('g19'), (cx(19) - 40, ry['g']), (cx(19) - 40, yG), (cx(19), yG)], C['gnd'], 8); badge(cx(19) - 40, ry['h'] + 18, 52, C['gnd'])
# wire 53: j24 -> +5 rail col 24
line([hp('j24'), (cx(24), y5)], C['v5'], 8); badge(cx(24), (ry['j'] + y5) / 2 + 24, 53, C['v5'])
# motor wires from motor (drawn above, right side) to g24 / g21
t(cx(22), ry['a'] - 4, '', 1)
mx, my = 1290, 560
a(f"<g filter='url(#sh)'><circle cx='{mx}' cy='{my}' r='70' fill='url(#alu)' stroke='#6b7280' stroke-width='4'/></g><circle cx='{mx}' cy='{my}' r='46' fill='none' stroke='#9ca3af' stroke-width='3'/><path d='M{mx-26} {my} a26 26 0 0 1 52 0' fill='#f97316' opacity='.9'/><text x='{mx}' y='{my+10}' font-size='30' font-weight='700' fill='#374151' text-anchor='middle' {SANS}>M</text>")
t(mx, my - 92, 'VIBRATION MOTOR', 20, '#0f172a', 700, 'middle'); t(mx + 84, my + 8, '3–5 V coin / pager', 15, '#475569', 400)
line([(mx - 20, my + 66), (mx - 20, ry['g'] + 8 - 120), (cx(24), ry['g'] + 8 - 120), hp('g24')], C['mRed'], 8)
line([(mx + 20, my + 66), (mx + 20, ry['g'] + 8 - 60), (cx(21) , ry['g'] - 60), hp('g21')], C['mBlue'], 8)
badge(mx - 20, my + 130, 54, C['mRed']); badge(mx + 20, my + 175, 55, C['mBlue'])
t(mx - 44, my + 96, 'red +', 16, C['mRed'], 700, 'end'); t(mx + 44, my + 96, 'blue −', 16, C['mBlue'], 700)
t(cx(c0), y5 + 110, 'Highlighted strips = holes joined inside the board (5 holes per strip)', 18, '#475569', 700)

# ============ 2: CIRCUIT ============
panel(1580, 140, 1380, 1290, '2', 'The circuit (why a transistor)')
sx, sy = 1700, 300
# +5V rail
a(f"<line x1='{sx+60}' y1='{sy+40}' x2='{sx+1100}' y2='{sy+40}' stroke='{C['v5']}' stroke-width='8'/>"); t(sx, sy + 48, '+5 V', 24, '#b45309', 700)
# GND rail
a(f"<line x1='{sx+60}' y1='{sy+780}' x2='{sx+1100}' y2='{sy+780}' stroke='{C['gnd']}' stroke-width='8'/>"); t(sx, sy + 788, 'GND', 24, '#111827', 700)
# motor + diode in parallel
mx2 = sx + 760
a(f"<line x1='{mx2}' y1='{sy+40}' x2='{mx2}' y2='{sy+190}' stroke='{C['mRed']}' stroke-width='8'/>")
a(f"<circle cx='{mx2}' cy='{sy+270}' r='80' fill='url(#alu)' stroke='#6b7280' stroke-width='4'/><text x='{mx2}' y='{sy+282}' font-size='34' font-weight='700' fill='#374151' text-anchor='middle' {SANS}>M</text>")
t(mx2 - 100, sy + 262, 'motor', 24, '#0f172a', 700, 'end'); t(mx2 - 100, sy + 290, 'red + up', 15, '#dc2626', 700, 'end'); t(mx2 - 100, sy + 312, 'blue − down', 15, '#2563eb', 700, 'end')
a(f"<line x1='{mx2}' y1='{sy+350}' x2='{mx2}' y2='{sy+520}' stroke='{C['mBlue']}' stroke-width='8'/>")
dx = mx2 + 200
a(f"<path d='M{mx2} {sy+110} H{dx} V{sy+176}' fill='none' stroke='{C['v5']}' stroke-width='8'/><path d='M{dx} {sy+460} V{sy+520} H{mx2}' fill='none' stroke='{C['mBlue']}' stroke-width='8'/>")
# diode symbol: cathode (stripe) toward +5 V
a(f"<path d='M{dx-34} {sy+255} L{dx+34} {sy+255} L{dx} {sy+190} Z' fill='#f59e0b'/><rect x='{dx-40}' y='{sy+176}' width='80' height='12' fill='#111'/>")
a(f"<path d='M{dx-34} {sy+180} L{dx+34} {sy+180}' stroke='#111' stroke-width='0'/>")
a(f"<line x1='{dx}' y1='{sy+255}' x2='{dx}' y2='{sy+460}' stroke='{C['mBlue']}' stroke-width='8'/>")
# fix diode orientation: current path from GND side up to +5 V (anode bottom, cathode top)
t(dx + 60, sy + 222, 'D1  1N4148', 22, '#0f172a', 700); t(dx + 60, sy + 250, 'absorbs the voltage spike', 16, '#475569'); t(dx + 60, sy + 272, 'when the motor stops', 16, '#475569'); t(dx + 60, sy + 298, 'stripe toward +5 V', 16, '#b45309', 700)
# transistor
tx, ty = sx + 560, sy + 620
a(f"<circle cx='{tx}' cy='{ty}' r='70' fill='#fff' stroke='#0f172a' stroke-width='5'/>")
a(f"<line x1='{tx-30}' y1='{ty-44}' x2='{tx-30}' y2='{ty+44}' stroke='#0f172a' stroke-width='8'/><line x1='{tx-30}' y1='{ty-20}' x2='{tx+30}' y2='{ty-50}' stroke='#0f172a' stroke-width='6'/><line x1='{tx-30}' y1='{ty+20}' x2='{tx+30}' y2='{ty+50}' stroke='#0f172a' stroke-width='6'/><path d='M{tx+30} {ty+50} l-20 -3 l10 -14 z' fill='#0f172a'/>")
a(f"<path d='M{tx+30} {ty-50} V{sy+520} H{mx2}' fill='none' stroke='{C['mBlue']}' stroke-width='8'/><path d='M{tx+30} {ty+50} V{sy+780}' fill='none' stroke='{C['gnd']}' stroke-width='8'/>")
t(tx + 50, ty - 30, 'C', 22, '#0f172a', 700); t(tx + 50, ty + 74, 'E', 22, '#0f172a', 700); t(tx - 130, ty - 58, 'B', 22, '#0f172a', 700)
t(tx, ty + 110, 'Q1  2N2222', 22, '#0f172a', 700, 'middle'); t(tx, ty + 136, 'a switch that D8 can flip', 15, '#475569', 400, 'middle')
# resistor + D8
a(f"<line x1='{sx+150}' y1='{ty}' x2='{sx+260}' y2='{ty}' stroke='{C['vib']}' stroke-width='8'/>")
a(f"<rect x='{sx+260}' y='{ty-20}' width='140' height='40' rx='16' fill='url(#res)'/>")
for k, bc in enumerate(('#7c4a1e', '#111', '#dc2626', '#d4af37')): rect(sx + 284 + k * 24 + (10 if k == 3 else 0), ty - 20, 9, 40, bc, 1)
a(f"<line x1='{sx+400}' y1='{ty}' x2='{tx-30}' y2='{ty}' stroke='{C['vib']}' stroke-width='8'/>")
t(sx + 330, ty - 34, 'R1  1 kΩ', 20, '#0f172a', 700, 'middle')
a(f"<circle cx='{sx+150}' cy='{ty}' r='11' fill='{C['vib']}'/>"); t(sx + 150, ty - 26, 'Nano D8', 22, '#c2410c', 700, 'middle')
t(sx, sy + 880, 'D8 HIGH  →  a little current into the base  →  Q1 opens  →  the motor gets its own current from 5 V and shakes.', 19, '#0f172a', 700)
t(sx, sy + 912, 'The Nano pin can give about 20 mA; the motor needs about 60–100 mA. So: NEVER motor straight to D8.', 19, '#b91c1c', 700)

# ============ 3: WHERE IT IS FIXED ============
panel(40, 1470, 2920, 910, '3', 'Where the vibration motor is fixed on the rig')
bx, by = 200, 1940
# base plate
a(f"<g filter='url(#sh)'><rect x='{bx}' y='{by+300}' width='1500' height='60' rx='8' fill='url(#wood)'/></g>")
for k in range(6): a(f"<circle cx='{bx+80+k*280}' cy='{by+330}' r='9' fill='#7c5a2a'/>")
t(bx + 750, by + 400, 'stiff base plate: plywood or acrylic, ~6 mm', 20, '#0f172a', 700, 'middle')
# pan motor
PX = 1030
a(f"<g filter='url(#sh)'><rect x='{bx+PX}' y='{by+130}' width='190' height='170' rx='14' fill='url(#mot)'/></g><rect x='{bx+PX+75}' y='{by+70}' width='40' height='64' rx='6' fill='url(#alu)'/>")
t(bx + PX + 95, by + 224, 'PAN', 22, '#e5e7eb', 700, 'middle'); t(bx + PX + 95, by + 250, 'NEMA17', 16, '#9ca3af', 400, 'middle')
# tilt head
a(f"<g filter='url(#sh)'><rect x='{bx+PX+30}' y='{by-90}' width='130' height='150' rx='12' fill='#334155'/></g><circle cx='{bx+PX+95}' cy='{by-15}' r='38' fill='#0b1a30' stroke='#4FC7EA' stroke-width='4'/><circle cx='{bx+PX+95}' cy='{by-15}' r='14' fill='#4FC7EA'/>")
t(bx + PX + 95, by - 108, 'camera + laser head', 20, '#0f172a', 700, 'middle')
# breadboard
a(f"<g filter='url(#sh)'><rect x='{bx+520}' y='{by+232}' width='420' height='68' rx='8' fill='url(#bb)' stroke='#cfcdc3' stroke-width='2'/></g>")
t(bx + 730, by + 272, 'breadboard', 18, '#475569', 700, 'middle')
# vibration motor + zip tie
vx2, vy2 = bx + 160, by + 226
a(f"<g filter='url(#sh)'><circle cx='{vx2}' cy='{vy2}' r='58' fill='url(#alu)' stroke='#6b7280' stroke-width='4'/></g><path d='M{vx2-26} {vy2} a26 26 0 0 1 52 0' fill='#f97316'/><text x='{vx2}' y='{vy2+12}' font-size='30' font-weight='700' fill='#374151' text-anchor='middle' {SANS}>M</text>")
a(f"<rect x='{vx2-70}' y='{vy2+56}' width='140' height='18' rx='4' fill='#e5e7eb' stroke='#94a3b8' stroke-width='2'/>")
for k in (-1, 1): a(f"<path d='M{vx2+k*36} {vy2-60} C {vx2+k*90} {vy2-30}, {vx2+k*90} {vy2+70}, {vx2+k*36} {vy2+90}' fill='none' stroke='#0f172a' stroke-width='7' stroke-linecap='round'/>")
t(vx2, vy2 - 92, 'VIBRATION MOTOR', 22, '#0f172a', 700, 'middle')
# wires to breadboard
a(f"<path d='M{vx2+56} {vy2-10} C {vx2+150} {vy2-190}, {bx+640} {vy2-150}, {bx+700} {by+232}' fill='none' stroke='{C['mRed']}' stroke-width='7'/><path d='M{vx2+56} {vy2+10} C {vx2+150} {vy2-120}, {bx+560} {vy2-110}, {bx+640} {by+232}' fill='none' stroke='{C['mBlue']}' stroke-width='7'/>")
t(vx2 + 330, vy2 - 214, 'two thin wires to holes g24 (red) and g21 (blue)', 18, '#0f172a', 700, 'middle')
# arrows shaking
for k in (-1, 1): a(f"<path d='M{vx2+k*95} {vy2-30} l{k*22} -14 m{-k*22} 14 l{k*22} 14' fill='none' stroke='#f97316' stroke-width='5' stroke-linecap='round'/>")
# numbered mounting steps
lx = bx + 1440
t(lx, by - 200, 'How to fix it', 28, '#0b1f3a', 700)
steps = [('1', 'Put it on the BASE PLATE, 10–15 cm from the pan motor. The plate carries the whole rig, so the whole rig shakes.'),
         ('2', 'Fix it flat with a cable tie AND a strip of double-sided foam tape. Bolt only if it comes with a mounting ear.'),
         ('3', 'Wires: 20–30 cm, run along the plate edge with tape. Keep them away from the pan shaft and the AS5600 magnet.'),
         ('4', 'Plug the red wire into g24 and the other wire into g21 (close-up, panel 1).'),
         ('5', 'Test with 12 V OFF: in the serial monitor type V1 → you feel a buzz, V0 → it stops.'),
         ('6', 'Demo moment: rig locked on the beacon → V1 → the lock box shakes but holds → V0.')]
for i, (n, s) in enumerate(steps):
    yy = by - 160 + i * 88
    rect(lx, yy, 48, 48, '#f97316', 12); t(lx + 24, yy + 34, n, 26, '#fff', 700, 'middle')
    words = s.split(' '); line1 = ''; lines = []
    for w in words:
        if len(line1 + w) > 66: lines.append(line1.strip()); line1 = ''
        line1 += w + ' '
    lines.append(line1.strip())
    for k, ln in enumerate(lines): t(lx + 66, yy + 20 + k * 24, ln, 17, '#0f172a')
a('</svg>')
svg = '\n'.join(o); open('vib.svg', 'w').write(svg)
open('vib.html', 'w').write(f"<!doctype html><html><head><meta charset='utf-8'><style>html,body{{margin:0}}svg{{display:block}}</style></head><body data-ready='1'>{svg}</body></html>")
print('ok')
