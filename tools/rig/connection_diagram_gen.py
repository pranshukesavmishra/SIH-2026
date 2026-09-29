"""Connection diagram (dark, like the wiring page): rails as buses, part boxes, net tags.
Same connections as the breadboard sheet, including the vibration circuit."""
W, H = 2400, 1560
BG = '#060b14'; PANEL = '#0a1220'; EDGE = '#1d2c44'; INK = '#c9d6e6'; DIM = '#6b7f99'
RED, ORG, GRY = '#ef4444', '#f59e0b', '#94a3b8'
STEP, DIR, SDA, SCL, LAS = '#a78bfa', '#f472b6', '#3b82f6', '#10b981', '#14b8a6'
o = []; a = o.append
MONO = "font-family='DejaVu Sans Mono,Liberation Mono,monospace'"
def t(x, y, s, sz=13, fill=INK, w=400, anc='start'): a(f"<text x='{x}' y='{y}' font-size='{sz}' font-weight='{w}' fill='{fill}' text-anchor='{anc}' {MONO}>{s}</text>")
def ln(pts, col, wd=3, dash=None):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    a(f"<path d='{d}' fill='none' stroke='{col}' stroke-width='{wd}' stroke-linejoin='round' stroke-linecap='round'" + (f" stroke-dasharray='{dash}'" if dash else '') + "/>")
def dot(x, y, col='#fbbf24'): a(f"<circle cx='{x}' cy='{y}' r='4.5' fill='{col}' stroke='#0a1220' stroke-width='1.5'/>")
def box(x, y, w, h, fill, stroke, title=None, tcol=None, tdy=-12):
    a(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{fill}' stroke='{stroke}' stroke-width='2'/>")
    if title: t(x + w / 2, y + tdy, title, 14, tcol or stroke, 700, 'middle')
def tag(x, y, s, col, right=True):
    dot(x, y, col)
    t(x + (12 if right else -12), y + 4, s, 12, col, 700, 'start' if right else 'end')

a(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'><rect width='{W}' height='{H}' fill='{BG}'/>")
t(40, 52, 'ZEROdrift · MK2 · connection diagram', 30, '#eaf4fd', 700)
t(40, 82, 'every connection of the breadboard sheet, drawn as a schematic · a tag (5V / GND) means: wire that pin to that rail', 14, DIM)

# ---- rails
RX0, RX1 = 500, 2160
for y, col, lab in ((400, RED, '+12 V rail'), (430, ORG, '5 V rail'), (460, GRY, 'GND rail')):
    ln([(RX0, y), (RX1, y)], col, 5); t(RX1 - 4, y - 8, lab, 13, col, 700, 'end')
t(RX0 + 4, 486, 'breadboard rails (or a WAGO block per rail)', 12, DIM)

# ---- power input
box(250, 290, 110, 64, PANEL, EDGE); t(305, 330, '12 V', 24, '#eaf4fd', 700, 'middle'); t(305, 282, 'adapter', 12, DIM, 400, 'middle')
a(f"<circle cx='430' cy='322' r='16' fill='{PANEL}' stroke='{INK}' stroke-width='2'/><circle cx='430' cy='322' r='5' fill='{INK}'/>"); t(430, 292, 'DC jack', 12, DIM, 400, 'middle')
ln([(360, 322), (414, 322)], INK, 3)
ln([(446, 322), (520, 322)], RED, 3); ln([(520, 322), (548, 300)], RED, 3); ln([(560, 322), (620, 322), (620, 400)], RED, 3)
t(540, 285, 'switch', 12, DIM, 400, 'middle'); dot(520, 322); dot(560, 322)
ln([(430, 338), (430, 460), (RX0, 460)], GRY, 3); t(440, 420, '−', 14, GRY, 700)

# ---- Arduino Nano
NX, NY, NW, NH = 560, 620, 150, 640
box(NX, NY, NW, NH, '#0d2350', '#3b6fd6'); t(NX + NW / 2, NY + 330, 'ARDUINO', 17, '#eaf4fd', 700, 'middle'); t(NX + NW / 2, NY + 352, 'NANO', 17, '#eaf4fd', 700, 'middle')
def npin(side, y, name):
    x = NX if side == 'L' else NX + NW; dot(x, y)
    t(x + (12 if side == 'L' else -12), y + 4, name, 13, '#eaf4fd', 700, 'start' if side == 'L' else 'end'); return (x, y)
n5 = npin('L', 690, '5V'); ng = npin('L', 730, 'GND'); na4 = npin('L', 1010, 'A4'); na5 = npin('L', 1050, 'A5')
d2 = npin('R', 690, 'D2'); d3 = npin('R', 720, 'D3'); d4 = npin('R', 1030, 'D4'); d5 = npin('R', 1060, 'D5'); d8 = npin('R', 1110, 'D8'); d7 = npin('R', 1140, 'D7')
ln([n5, (520, 690), (520, 430), (RX0, 430)], ORG, 3)
ln([ng, (500, 730), (500, 470), (500, 460)], GRY, 3)
ln([(NX + 75, NY + NH), (NX + 75, 1330)], '#cbd5e1', 3); t(NX + 85, 1290, 'USB-C', 12, DIM)

# ---- drivers
def driver(y0, name, stepc, dirc, capx, capy, tag_):
    X = 1000
    box(X, y0, 140, 290, '#082018', '#22c55e', name, '#4ade80', -14)
    a(f"<rect x='{X+50}' y='{y0+100}' width='40' height='40' rx='4' fill='#0d3a2a' stroke='#22c55e'/>"); t(X + 70, y0 + 125, 'A4988', 10, '#4ade80', 700, 'middle')
    L = ['EN', 'MS1', 'MS2', 'MS3', 'RST', 'SLP', 'STEP', 'DIR']; R = ['VMOT', 'GND', '2B', '2A', '1A', '1B', 'VDD', 'GND']
    P = {}
    for i, (l, r) in enumerate(zip(L, R)):
        y = y0 + 40 + i * 28
        dot(X, y); t(X + 12, y + 4, l, 12, '#d1fae5', 700); dot(X + 140, y); t(X + 128, y + 4, r, 12, '#d1fae5', 700, 'end')
        P['L' + l] = (X, y); P['R' + r + ('2' if i == 7 else '')] = (X + 140, y)
    tag(X - 24, P['LEN'][1], 'GND', GRY, False); ln([(X - 24, P['LEN'][1]), P['LEN']], GRY, 2)
    for m in ('MS1', 'MS2', 'MS3'): tag(X - 24, P['L' + m][1], '5V', ORG, False); ln([(X - 24, P['L' + m][1]), P['L' + m]], ORG, 2)
    ln([P['LRST'], (X - 18, P['LRST'][1]), (X - 18, P['LSLP'][1]), P['LSLP']], STEP if False else '#c4b5fd', 2)
    tag(X + 164, P['RVDD'][1], '5V', ORG); ln([P['RVDD'], (X + 164, P['RVDD'][1])], ORG, 2)
    tag(X + 164, P['RGND2'][1], 'GND', GRY); ln([P['RGND2'], (X + 164, P['RGND2'][1])], GRY, 2)
    ln([P['RVMOT'], (capx, P['RVMOT'][1]), (capx, 400)], RED, 3)
    ln([P['RGND'], (capx + 20, P['RGND'][1]), (capx + 20, 460)], GRY, 3)
    a(f"<rect x='{capx-2}' y='{capy}' width='24' height='40' rx='5' fill='#1d4ed8' stroke='#93c5fd' stroke-width='1.5'/>"); t(capx + 34, capy + 24, tag_, 12, '#93c5fd', 700)
    return P
PAN = driver(600, 'PAN DRIVER (bottom motor)', STEP, DIR, 1200, 520, 'C1 100µF')
TILT = driver(940, 'TILT DRIVER (top motor)', STEP, DIR, 1250, 840, 'C2 100µF')
# STEP / DIR
def sd(np_, dp, col, xc):
    ln([np_, (xc, np_[1]), (xc, dp[1]), dp], col, 3)
sd(d2, PAN['LSTEP'], STEP, 800); sd(d3, PAN['LDIR'], DIR, 830); sd(d4, TILT['LSTEP'], STEP, 860); sd(d5, TILT['LDIR'], DIR, 890)

# ---- motors
def motor(x, y, name, P):
    box(x, y, 150, 150, '#101826', '#334155'); a(f"<circle cx='{x+75}' cy='{y+75}' r='34' fill='#1f2937' stroke='#475569' stroke-width='2'/><circle cx='{x+75}' cy='{y+75}' r='12' fill='#94a3b8'/>")
    t(x + 75, y + 176, name, 13, DIM, 700, 'middle')
    cols = (('2B', '#22c55e'), ('2A', '#94a3b8'), ('1A', '#ef4444'), ('1B', '#3b82f6'))
    for k, (pin, col) in enumerate(cols):
        yy = y + 22 + k * 32; src = P['R' + pin]
        xm = 1360 + k * 22 + (0 if P is PAN else 0)
        ln([src, (xm, src[1]), (xm, yy), (x, yy)], col, 3); dot(x, yy, col)
        t(x - 8, yy - 6, pin, 11, col, 700, 'end')
motor(1600, 600, 'PAN motor (bottom)', PAN); motor(1600, 940, 'TILT motor (top)', TILT)
t(1780, 700, 'coil pairs: black+green = one pair,', 12, DIM); t(1780, 718, 'red+blue = the other (measure Ω first)', 12, DIM)

# ---- multiplexer + AS5600
box(230, 900, 170, 150, '#0d1f3f', '#1e40af', 'MULTIPLEXER TCA9548A', '#93c5fd', -14)
def mp(side, y, name, col=None):
    x = 230 if side == 'L' else 400; dot(x, y); t(x + (12 if side == 'L' else -12), y + 4, name, 12, '#dbeafe', 700, 'start' if side == 'L' else 'end'); return (x, y)
mv = mp('L', 930, 'VIN'); mg = mp('L', 960, 'GND'); ma = mp('L', 990, 'A0-2'); tag(206, 930, '5V', ORG, False); ln([(206, 930), mv], ORG, 2)
tag(206, 960, 'GND', GRY, False); ln([(206, 960), mg], GRY, 2); tag(206, 990, 'GND', GRY, False); ln([(206, 990), ma], GRY, 2)
msda = mp('R', 950, 'SDA'); mscl = mp('R', 990, 'SCL')
ln([msda, (450, 950), (450, na4[1]), na4], SDA, 3); ln([mscl, (480, 990), (480, na5[1]), na5], SCL, 3)
t(300, 1045, 'SD0', 11, '#dbeafe', 700, 'middle'); t(350, 1045, 'SC0', 11, '#dbeafe', 700, 'middle'); dot(300, 1050); dot(350, 1050)
box(220, 1200, 200, 90, '#2a1259', '#7c3aed', 'AS5600 (pan sensor)', '#c4b5fd', 112)
for x, nm, col in ((262, 'SDA', SDA), (312, 'SCL', SCL)):
    dot(x, 1200); t(x, 1222, nm, 12, '#ede9fe', 700, 'middle')
ln([(300, 1050), (300, 1150), (262, 1150), (262, 1200)], SDA, 3); ln([(350, 1050), (350, 1130), (312, 1130), (312, 1200)], SCL, 3)
for y, nm, tg, col in ((1215, 'VCC', '5V', ORG), (1243, 'GND', 'GND', GRY), (1271, 'DIR', 'GND', GRY)):
    dot(420, y); t(408, y + 4, nm, 12, '#ede9fe', 700, 'end'); tag(444, y, tg, col); ln([(420, y), (444, y)], col, 2)

# ---- laser + laptop
box(780, 1330, 130, 84, '#111827', '#475569', 'LASER KY-008', '#94a3b8', -10)
for y, nm in ((1348, 'S'), (1372, 'mid'), (1396, '−')): dot(780, y); t(792, y + 4, nm, 12, '#e5e7eb', 700)
ln([d7, (740, 1140), (740, 1348), (780, 1348)], LAS, 3); t(700, 1372, '×', 16, DIM, 700, 'end'); tag(756, 1396, 'GND', GRY, False); ln([(756, 1396), (780, 1396)], GRY, 2)
box(520, 1330, 170, 84, PANEL, EDGE); t(605, 1366, 'LAPTOP', 14, DIM, 700, 'middle'); t(605, 1390, 'Chrome · live page', 12, DIM, 400, 'middle')

# ---- vibration circuit
ln([d8, (760, 1110), (760, 1290), (1380, 1290), (1380, 1360), (1400, 1360)], '#f97316', 3)
a("<g transform='translate(0,60)'>")
t(1420, 1082, 'VIBRATION MOTOR CIRCUIT', 14, '#fb923c', 700)
a(f"<rect x='1400' y='1288' width='120' height='24' rx='10' fill='#c9a86a'/>"); t(1460, 1278, 'R1 1 kΩ', 12, '#fdba74', 700, 'middle')
ln([(1520, 1300), (1570, 1300)], '#f97316', 3)
QX, QY = 1620, 1300
a(f"<circle cx='{QX}' cy='{QY}' r='46' fill='none' stroke='{INK}' stroke-width='2'/><line x1='{QX-16}' y1='{QY-26}' x2='{QX-16}' y2='{QY+26}' stroke='{INK}' stroke-width='5'/><line x1='{QX-16}' y1='{QY-12}' x2='{QX+18}' y2='{QY-34}' stroke='{INK}' stroke-width='3'/><line x1='{QX-16}' y1='{QY+12}' x2='{QX+18}' y2='{QY+34}' stroke='{INK}' stroke-width='3'/><path d='M{QX+18} {QY+34} l-14 -2 l6 -10 z' fill='{INK}'/>")
ln([(1570, 1300), (QX - 16, 1300)], '#f97316', 3)
t(QX + 56, QY - 6, 'C', 12, DIM, 700); t(QX + 56, QY + 20, 'E', 12, DIM, 700); t(QX - 60, QY - 10, 'B', 12, DIM, 700); t(QX - 30, QY + 76, 'Q1 2N2222', 12, '#e5e7eb', 700, 'end')
MX, MY = 1620, 1180
a(f"<circle cx='{MX}' cy='{MY}' r='38' fill='#1f2937' stroke='#94a3b8' stroke-width='3'/><text x='{MX}' y='{MY+9}' font-size='26' font-weight='700' fill='#e5e7eb' text-anchor='middle' {MONO}>M</text>")
t(MX - 52, MY + 6, 'vibration motor', 12, '#e5e7eb', 700, 'end')
ln([(MX, QY - 34), (MX, MY + 38)], '#3b82f6', 3); t(MX - 10, 1246, '− blue', 11, '#3b82f6', 700, 'end')
tag(MX, 1110, '5V', ORG); ln([(MX, MY - 38), (MX, 1110)], '#ef4444', 3); t(MX - 12, 1130, '+ red', 11, '#ef4444', 700, 'end')
DX = 1740
ln([(MX, 1116), (DX, 1116), (DX, 1150)], ORG, 2); ln([(DX, 1250), (DX, 1266), (MX, 1266)], '#3b82f6', 2)
a(f"<path d='M{DX-16} {1240} L{DX+16} {1240} L{DX} {1190} Z' fill='#f59e0b'/><rect x='{DX-18}' y='1182' width='36' height='7' fill='#111'/>"); ln([(DX, 1150), (DX, 1182)], ORG, 2); ln([(DX, 1240), (DX, 1250)], '#3b82f6', 2)
t(DX + 28, 1218, 'D1 1N4148 (stripe → 5V)', 12, '#fbbf24', 700)
tag(QX + 20, QY + 34 + 30, 'GND', GRY); ln([(QX + 18, QY + 34), (QX + 18, QY + 64)], GRY, 3)
t(1420, 1420, 'serial:  V1 = shake ON · V0 = OFF', 13, '#fdba74', 700)

a('</g>')
# ---- legend
lx, ly = 1700, 150
for i, (col, nm) in enumerate(((RED, '+12 V'), (ORG, '5 V'), (GRY, 'GND'), (STEP, 'STEP'), (DIR, 'DIR'), (SDA, 'SDA'), (SCL, 'SCL'), (LAS, 'laser signal'), ('#f97316', 'D8 · vibration'), ('#cbd5e1', 'USB'))):
    x = lx + (i % 2) * 240; y = ly + (i // 2) * 30
    ln([(x, y), (x + 40, y)], col, 4); t(x + 52, y + 5, nm, 13, INK)
a('</svg>')
svg = '\n'.join(o); open('conn.svg', 'w').write(svg)
open('conn.html', 'w').write(f"<!doctype html><html><head><meta charset='utf-8'><style>html,body{{margin:0;background:#060b14}}svg{{display:block}}</style></head><body data-ready='1'>{svg}</body></html>")
print('ok')
