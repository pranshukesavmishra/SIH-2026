"""Hardware circuit infographics for the SOP page (MK1 working prototype, MK2 in development).

Draws every part as a picture, every wire in its colour, and the component list,
colour guide, how-it-works and key-features panels. Output: SVG + HTML wrapper;
render the HTML to PNG with Playwright (see __main__).
Pin assignments follow tools/rig/rig_firmware.ino (MK1) and rig_firmware_v2.ino /
docs/wiring_plan.js (MK2).
"""
import os, sys

FONT = "'ZD Inter', 'Inter', Arial, sans-serif"
MONO = "'DejaVu Sans Mono', Menlo, monospace"
W, H = 2400, 1560
COL = {'5v': '#e0302c', 'gnd': '#1d1d1f', '12v': '#c2410c', 'sig': '#f59e0b', 'step': '#7c3aed', 'dir': '#db2777',
       'sda': '#2563eb', 'scl': '#16a34a', 'usb': '#6b7280', 'laser': '#0d9488', 'vib': '#ea580c',
       'c1': '#1d1d1f', 'c2': '#16a34a', 'c3': '#dc2626', 'c4': '#2563eb'}


class S:
    def __init__(self):
        self.o = []

    def a(self, s):
        self.o.append(s)

    def t(self, x, y, s, size=18, fill='#1d1d1f', w=500, anc='start', font=FONT, extra=''):
        self.a(f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{w}' fill='{fill}' text-anchor='{anc}' font-family=\"{font}\" {extra}>{s}</text>")

    def wire(self, pts, col, width=5.5):
        d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
        self.a(f"<path d='{d}' fill='none' stroke='#fff' stroke-width='{width + 4}' stroke-linejoin='round' stroke-linecap='round'/>")
        self.a(f"<path d='{d}' fill='none' stroke='{col}' stroke-width='{width}' stroke-linejoin='round' stroke-linecap='round'/>")

    def dot(self, x, y, col='#d4a017', r=5.5):
        self.a(f"<circle cx='{x}' cy='{y}' r='{r}' fill='{col}' stroke='#7a5a00' stroke-width='1.2'/>")

    def tag(self, x, y, s, col, anc='start', size=15):
        w = len(s) * size * 0.58 + 16
        x0 = x if anc == 'start' else (x - w if anc == 'end' else x - w / 2)
        self.a(f"<rect x='{x0:.1f}' y='{y - size + 1:.1f}' width='{w:.1f}' height='{size + 9}' rx='6' fill='#fff' stroke='{col}' stroke-width='2'/>")
        self.t(x0 + w / 2, y + 3, s, size, col, 700, 'middle', MONO)

    def banner(self, x, y, w, h, s, fill='#0b3a75', size=24):
        self.a(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{h / 2}' fill='{fill}'/>")
        self.t(x + w / 2, y + h / 2 + size * .36, s, size, '#fff', 700, 'middle')

    def panel(self, x, y, w, h, title, col):
        self.a(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='16' fill='#fff' stroke='{col}' stroke-width='2.5'/>")
        tw = len(title) * 13.2 + 40
        self.a(f"<path d='M{x} {y + 16} a16 16 0 0 1 16 -16 h{tw - 16} v46 h{-tw} z' fill='{col}'/>")
        self.t(x + 20, y + 32, title, 22, '#fff', 700)

    def svg(self):
        return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>" + DEFS +
                ''.join(self.o) + '</svg>')


DEFS = """<defs>
<linearGradient id='pcbBlue' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#2a73d9'/><stop offset='1' stop-color='#123f86'/></linearGradient>
<linearGradient id='pcbRed' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#e2433b'/><stop offset='1' stop-color='#9f1d17'/></linearGradient>
<linearGradient id='pcbPurple' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#8b5cf6'/><stop offset='1' stop-color='#4c1d95'/></linearGradient>
<linearGradient id='pcbBlack' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#3a3a3e'/><stop offset='1' stop-color='#141416'/></linearGradient>
<linearGradient id='metal' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#e9ebef'/><stop offset='.5' stop-color='#a9aeb7'/><stop offset='1' stop-color='#6b717c'/></linearGradient>
<linearGradient id='metalDark' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#5b6068'/><stop offset='1' stop-color='#26292e'/></linearGradient>
<linearGradient id='servoBlue' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#3b82f6'/><stop offset='1' stop-color='#1e40af'/></linearGradient>
<linearGradient id='brass' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#f6d67a'/><stop offset='.5' stop-color='#c79a2b'/><stop offset='1' stop-color='#8a6512'/></linearGradient>
<linearGradient id='capBlue' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#1e3a8a'/><stop offset='.45' stop-color='#3b82f6'/><stop offset='1' stop-color='#1e3a8a'/></linearGradient>
<linearGradient id='screen' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#0b1b33'/><stop offset='1' stop-color='#050b16'/></linearGradient>
<radialGradient id='glow'><stop offset='0' stop-color='#fff' stop-opacity='1'/><stop offset='.35' stop-color='#fff7c2' stop-opacity='.8'/><stop offset='1' stop-color='#ffe066' stop-opacity='0'/></radialGradient>
<filter id='sh' x='-10%' y='-10%' width='130%' height='140%'><feDropShadow dx='0' dy='6' stdDeviation='7' flood-color='#0b1b33' flood-opacity='.22'/></filter>
</defs>"""


# ---------------------------------------------------------------- parts
def nano(s, x, y, top, bottom, w=380, h=150, label='ARDUINO NANO'):
    """Horizontal Nano. top/bottom: list of pin names (None = unused pin). Returns {name: (x, y)} of pin tips."""
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='url(#pcbBlue)' stroke='#0b2f66' stroke-width='2'/></g>")
    s.a(f"<rect x='{x - 26}' y='{y + h / 2 - 26}' width='44' height='52' rx='4' fill='url(#metal)' stroke='#6b717c'/>")  # mini-USB
    s.a(f"<rect x='{x + w / 2 - 44}' y='{y + h / 2 - 34}' width='88' height='68' rx='4' fill='#111' stroke='#333'/>")
    s.t(x + w / 2, y + h / 2 + 5, 'ATmega328P', 12, '#9aa3ad', 600, 'middle', MONO)
    s.t(x + w / 2 + 58, y + h / 2 + 6, label, 15, '#dbeafe', 800, 'start')
    pins = {}
    for row, names, py in ((0, top, y + 16), (1, bottom, y + h - 16)):
        n = len(names); step = (w - 60) / (n - 1)
        for i, nm in enumerate(names):
            px = x + 40 + i * step
            s.a(f"<rect x='{px - 7}' y='{py - 7}' width='14' height='14' rx='2' fill='#1b1b1b'/>")
            s.dot(px, py, '#e8c547' if nm else '#8a7a3a', 4.2)
            if nm:
                s.t(px, py + (22 if row == 0 else -12), nm, 12, '#fff', 700, 'middle', MONO)
                pins[nm] = (px, py)
    return pins


def servo(s, x, y, name, w=170, h=96):
    """SG90 seen from the side. Returns wire exits: brown, red, orange (bottom)."""
    s.a(f"<g filter='url(#sh)'><rect x='{x - 22}' y='{y + 20}' width='{w + 44}' height='14' rx='4' fill='#2451b8'/>"
        f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='url(#servoBlue)' stroke='#172f7a' stroke-width='2'/></g>")
    s.a(f"<circle cx='{x + 50}' cy='{y - 8}' r='24' fill='#e5e7eb' stroke='#9ca3af' stroke-width='2'/>")
    s.a(f"<rect x='{x + 20}' y='{y - 20}' width='64' height='16' rx='8' fill='#f9fafb' stroke='#9ca3af' stroke-width='1.5'/>")
    s.a(f"<circle cx='{x + 50}' cy='{y - 8}' r='5' fill='#6b7280'/>")
    s.t(x + w / 2, y + h / 2 + 8, 'SG90', 20, '#dbeafe', 800, 'middle')
    s.t(x + w / 2 + 40, y - 30, name, 18, '#1d1d1f', 700, 'start')
    ex = []
    for i, c in enumerate(('#6b3e1f', '#e0302c', '#f59e0b')):
        px = x + w - 46 + i * 14
        s.a(f"<rect x='{px - 4}' y='{y + h - 2}' width='8' height='16' fill='{c}'/>")
        ex.append((px, y + h + 12))
    return ex


def laser(s, x, y, w=150, h=80, lab='below'):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='url(#pcbBlack)' stroke='#000' stroke-width='1.5'/></g>")
    s.a(f"<rect x='{x + 28}' y='{y - 34}' width='44' height='40' rx='6' fill='url(#brass)' stroke='#7a5a12'/>")
    s.a(f"<circle cx='{x + 50}' cy='{y - 34}' r='8' fill='#ff3b30'/><circle cx='{x + 50}' cy='{y - 34}' r='22' fill='#ff3b30' opacity='.18'/>")
    s.t(x + w - 12, y + 28, 'KY-008', 15, '#e5e7eb', 700, 'end')
    pins = {}
    for i, nm in enumerate(('S', '+', '−')):
        px = x + 36 + i * 38
        s.dot(px, y + h - 12, '#e8c547', 4.5); s.t(px, y + h - 24, nm, 13, '#fff', 700, 'middle', MONO)
        pins[nm] = (px, y + h - 12)
    if lab == 'below':
        s.t(x + w / 2, y + h + 30, 'Laser · 650 nm', 17, '#1d1d1f', 700, 'middle')
    elif lab == 'left':
        s.t(x - 14, y + 30, 'Laser', 17, '#1d1d1f', 700, 'end'); s.t(x - 14, y + 50, '650 nm', 14, '#6b7280', 500, 'end')
    else:
        s.t(x + 84, y - 14, 'Laser · 650 nm', 15, '#1d1d1f', 700, 'start')
    return pins


def laptop(s, x, y, w=330, label='Laptop · ZeroDrift in the browser', cam=True):
    h = w * .62
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='#1f2937'/>"
        f"<rect x='{x + 12}' y='{y + 14}' width='{w - 24}' height='{h - 26}' rx='4' fill='url(#screen)'/>"
        f"<path d='M{x - 30} {y + h} h{w + 60} l-18 22 h{-w - 24} z' fill='url(#metal)'/></g>")
    if cam:
        s.a(f"<circle cx='{x + w / 2}' cy='{y + 7}' r='4' fill='#4FC7EA'/>")
    # little UI: lock box + reticle
    cx, cy = x + w * .45, y + h * .5
    s.a(f"<path d='M{cx - 26} {cy - 14} v-12 h12 M{cx + 26} {cy - 14} v-12 h-12 M{cx - 26} {cy + 14} v12 h12 M{cx + 26} {cy + 14} v12 h-12' stroke='#5DE08A' stroke-width='3' fill='none'/>")
    s.a(f"<circle cx='{cx}' cy='{cy}' r='6' fill='#fff'/><circle cx='{cx}' cy='{cy}' r='16' fill='url(#glow)'/>")
    s.t(x + 22, y + 38, '● LOCKED  4.0 Hz', 13, '#5DE08A', 700, 'start', MONO)
    s.a(f"<rect x='{x + w - 96}' y='{y + 30}' width='72' height='{h - 70}' rx='4' fill='#0e2340'/>")
    for i in range(5):
        s.a(f"<rect x='{x + w - 88}' y='{y + 42 + i * 18}' width='56' height='8' rx='3' fill='#1e3a5f'/>")
    s.t(x + w / 2, y + h + 56, label, 17, '#1d1d1f', 700, 'middle')
    return (x + w + 30, y + h + 8)   # USB port position (right side of base)


def phone(s, x, y):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='64' height='120' rx='12' fill='#111827'/><rect x='{x + 5}' y='{y + 8}' width='54' height='100' rx='6' fill='#1f2937'/></g>")
    s.a(f"<circle cx='{x + 32}' cy='{y + 36}' r='44' fill='url(#glow)'/><circle cx='{x + 32}' cy='{y + 36}' r='9' fill='#fff'/>")
    s.t(x + 32, y + 150, 'Beacon', 17, '#1d1d1f', 700, 'middle')
    s.t(x + 32, y + 172, 'phone torch · 4 Hz', 14, '#6b7280', 500, 'middle')


def a4988(s, x, y, name):
    w, h = 170, 250
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='url(#pcbRed)' stroke='#7f1d1d' stroke-width='2'/></g>")
    s.a(f"<rect x='{x + 45}' y='{y + 78}' width='80' height='80' rx='4' fill='url(#metal)' stroke='#6b717c'/>")
    for i in range(6):
        s.a(f"<rect x='{x + 51 + i * 12.5}' y='{y + 84}' width='6' height='68' rx='2' fill='#c7ccd4'/>")
    s.t(x + w / 2, y + h - 16, 'A4988', 16, '#fee2e2', 800, 'middle')
    L = ['EN', 'MS1', 'MS2', 'MS3', 'RST', 'SLP', 'STEP', 'DIR']; R = ['VMOT', 'GND', '2B', '2A', '1A', '1B', 'VDD', 'GND2']
    pins = {}
    for i, (l, r) in enumerate(zip(L, R)):
        py = y + 24 + i * 27
        s.dot(x + 10, py, '#e8c547', 4); s.t(x + 20, py + 4, l, 11, '#fff', 700, 'start', MONO); pins[l] = (x + 10, py)
        s.dot(x + w - 10, py, '#e8c547', 4); s.t(x + w - 20, py + 4, r.replace('GND2', 'GND'), 11, '#fff', 700, 'end', MONO); pins[r] = (x + w - 10, py)
    s.t(x + w / 2, y + h + 28, name, 17, '#1d1d1f', 700, 'middle')
    return pins


def nema(s, x, y, name, sz=170):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{sz}' height='{sz}' rx='14' fill='url(#metalDark)'/>"
        f"<rect x='{x + 14}' y='{y + 14}' width='{sz - 28}' height='{sz - 28}' rx='10' fill='url(#metal)'/></g>")
    c = sz / 2
    s.a(f"<circle cx='{x + c}' cy='{y + c}' r='34' fill='#d1d5db' stroke='#9ca3af' stroke-width='3'/><circle cx='{x + c}' cy='{y + c}' r='10' fill='#6b7280'/>")
    for dx, dy in ((22, 22), (sz - 22, 22), (22, sz - 22), (sz - 22, sz - 22)):
        s.a(f"<circle cx='{x + dx}' cy='{y + dy}' r='6' fill='#4b5563'/>")
    s.t(x + c, y + sz + 30, name, 17, '#1d1d1f', 700, 'middle')
    s.t(x + c, y + sz + 50, 'NEMA 17 stepper', 14, '#6b7280', 500, 'middle')
    ex = []
    for i, col in enumerate((COL['c1'], COL['c2'], COL['c3'], COL['c4'])):
        ex.append((x - 2, y + 40 + i * 30)); s.a(f"<rect x='{x - 10}' y='{y + 36 + i * 30}' width='12' height='8' fill='{col}'/>")
    return ex


def cap(s, x, y, label='100 µF'):
    s.a(f"<rect x='{x - 16}' y='{y}' width='32' height='52' rx='6' fill='url(#capBlue)' stroke='#1e3a8a'/>")
    s.a(f"<rect x='{x + 6}' y='{y + 4}' width='7' height='44' fill='#cbd5e1' opacity='.75'/>")
    s.t(x, y - 10, label, 13, '#1e3a8a', 700, 'middle', MONO)


def small_board(s, x, y, w, h, fill, title, pins, pin_side='left', title_col='#e0e7ff'):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{fill}' stroke='#0b1b33' stroke-width='1.5'/></g>")
    s.t(x + w / 2, y + h - 12, title, 14, title_col, 800, 'middle')
    out = {}
    groups = {}
    for nm in pins:
        nm, _, sd = nm.partition(':'); groups.setdefault(sd or pin_side, []).append(nm)
    for pin_side, names in groups.items():
        _pins(s, x, y, w, h, names, pin_side, out)
    return out


def _pins(s, x, y, w, h, pins, pin_side, out):
    n = len(pins)
    for i, nm in enumerate(pins):
        if pin_side == 'left':
            px, py = x + 10, y + 22 + i * ((h - 44) / max(1, n - 1))
            s.dot(px, py, '#e8c547', 4); s.t(px + 12, py + 4, nm, 11, '#fff', 700, 'start', MONO)
        elif pin_side == 'right':
            px, py = x + w - 10, y + 22 + i * ((h - 44) / max(1, n - 1))
            s.dot(px, py, '#e8c547', 4); s.t(px - 12, py + 4, nm, 11, '#fff', 700, 'end', MONO)
        else:  # top
            px, py = x + 24 + i * ((w - 48) / max(1, n - 1)), y + 12
            s.dot(px, py, '#e8c547', 4); s.t(px, py + 20, nm, 11, '#fff', 700, 'middle', MONO)
        out[nm] = (px, py)


def usbcam(s, x, y):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='120' height='66' rx='14' fill='#1f2937'/></g>")
    s.a(f"<circle cx='{x + 60}' cy='{y + 33}' r='22' fill='#0b1220' stroke='#4b5563' stroke-width='3'/><circle cx='{x + 60}' cy='{y + 33}' r='9' fill='#2563eb'/><circle cx='{x + 56}' cy='{y + 29}' r='3' fill='#bfdbfe'/>")
    s.t(x + 60, y + 96, 'USB camera', 17, '#1d1d1f', 700, 'middle')
    s.t(x + 60, y + 116, 'USB → laptop', 14, '#6b7280', 600, 'middle', MONO)
    return (x + 120, y + 33)


def adapter(s, x, y):
    s.a(f"<g filter='url(#sh)'><rect x='{x}' y='{y}' width='130' height='84' rx='10' fill='#111827'/></g>")
    s.t(x + 65, y + 50, '12 V · 2 A', 18, '#f9fafb', 800, 'middle')
    s.t(x + 65, y + 112, 'Adapter', 16, '#1d1d1f', 700, 'middle')
    return (x + 130, y + 42)


def jack_switch(s, x, y):
    s.a(f"<rect x='{x}' y='{y}' width='70' height='56' rx='8' fill='#1f2937'/><circle cx='{x + 35}' cy='{y + 28}' r='14' fill='#0b0b0b' stroke='#6b7280' stroke-width='3'/><circle cx='{x + 35}' cy='{y + 28}' r='4' fill='#9ca3af'/>")
    s.t(x + 35, y - 12, 'DC jack', 14, '#1d1d1f', 700, 'middle')
    sx = x + 130
    s.a(f"<rect x='{sx}' y='{y + 4}' width='66' height='48' rx='8' fill='#111827'/><rect x='{sx + 10}' y='{y + 14}' width='46' height='28' rx='5' fill='#dc2626'/><rect x='{sx + 30}' y='{y + 14}' width='26' height='28' rx='5' fill='#fca5a5'/>")
    s.t(sx + 33, y - 12, 'Kill switch', 14, '#1d1d1f', 700, 'middle')
    return (x, y + 28), (x + 70, y + 28), (sx, y + 28), (sx + 66, y + 28)


def vib(s, x, y):
    s.a(f"<circle cx='{x}' cy='{y}' r='30' fill='url(#metal)' stroke='#6b717c' stroke-width='2'/><circle cx='{x}' cy='{y}' r='12' fill='#9ca3af'/>")
    s.a(f"<path d='M{x + 38} {y - 16} q6 16 0 32 M{x + 48} {y - 24} q10 24 0 48' stroke='#ea580c' stroke-width='3' fill='none'/>")
    s.t(x, y + 54, 'Vibration motor', 15, '#1d1d1f', 700, 'middle')
    s.t(x, y + 72, 'via 2N2222 + 1 kΩ', 13, '#6b7280', 500, 'middle')
    return (x - 30, y), (x, y - 30)


# ---------------------------------------------------------------- common panels
def panels(s, guide, how, feats, comps, soon=False, final_img=None, final_title='Final build', pinmap=None):
    # final build picture (top right)
    fx, fy, fw, fh = 1770, 118, 590, 470
    s.a(f"<rect x='{fx}' y='{fy}' width='{fw}' height='{fh}' rx='18' fill='#0b0f19'/>")
    if final_img:
        s.a(f"<image href='{final_img}' x='{fx}' y='{fy}' width='{fw}' height='{fh}' preserveAspectRatio='xMidYMid slice' clip-path='inset(0 round 18px)'/>")
    s.banner(fx + 20, fy - 22, 290, 46, final_title, '#0b3a75', 21)
    if soon:
        s.a(f"<rect x='{fx + fw - 230}' y='{fy + fh - 58}' width='210' height='40' rx='20' fill='#fff7e6' stroke='#f59e0b' stroke-width='2'/>")
        s.t(fx + fw - 125, fy + fh - 32, '● Coming soon', 18, '#b45309', 800, 'middle')
    # component list (right)
    cx, cy, cw = 1770, 628, 590
    ch = 64 + 38 * len(comps)
    s.a(f"<rect x='{cx}' y='{cy}' width='{cw}' height='{ch}' rx='16' fill='#fff' stroke='#6d28d9' stroke-width='2.5'/>")
    s.a(f"<path d='M{cx} {cy + 16} a16 16 0 0 1 16 -16 h{cw - 32} a16 16 0 0 1 16 16 v34 h{-cw} z' fill='#6d28d9'/>")
    s.t(cx + 20, cy + 34, 'Component list', 22, '#fff', 700)
    s.t(cx + cw - 20, cy + 34, 'Qty', 18, '#fff', 700, 'end')
    for i, (nm, q) in enumerate(comps):
        yy = cy + 50 + i * 38
        if i % 2 == 0:
            s.a(f"<rect x='{cx + 2}' y='{yy}' width='{cw - 4}' height='38' fill='#f5f3ff'/>")
        s.t(cx + 22, yy + 25, f'{i + 1}', 16, '#6d28d9', 800, 'start')
        s.t(cx + 56, yy + 25, nm, 16, '#1d1d1f', 500)
        s.t(cx + cw - 22, yy + 25, q, 16, '#1d1d1f', 700, 'end')
    # pin map (under the component list)
    if pinmap:
        py0 = cy + ch + 28; ph = 1530 - py0
        s.a(f"<rect x='{cx}' y='{py0}' width='{cw}' height='{ph}' rx='16' fill='#fff' stroke='#0b3a75' stroke-width='2.5'/>")
        s.a(f"<path d='M{cx} {py0 + 16} a16 16 0 0 1 16 -16 h{cw - 32} a16 16 0 0 1 16 16 v34 h{-cw} z' fill='#0b3a75'/>")
        s.t(cx + 20, py0 + 34, 'Pin map', 22, '#fff', 700)
        rh = min(40, (ph - 64) / len(pinmap))
        for i, (pin, col, what) in enumerate(pinmap):
            yy = py0 + 62 + i * rh
            s.a(f"<rect x='{cx + 20}' y='{yy}' width='88' height='{rh - 10}' rx='7' fill='{col}'/>")
            s.t(cx + 64, yy + (rh - 10) / 2 + 5, pin, 14, '#fff', 800, 'middle', MONO)
            s.t(cx + 126, yy + (rh - 10) / 2 + 6, what, 16, '#1d1d1f', 500)
    # bottom panels
    y0 = 1140
    s.panel(40, y0, 520, 390, 'Wiring colour guide', '#0b3a75')
    for i, (col, nm) in enumerate(guide):
        yy = y0 + 86 + i * 36
        s.a(f"<path d='M70 {yy} h70' stroke='{col}' stroke-width='7' stroke-linecap='round'/>")
        s.t(160, yy + 6, nm, 17, '#1d1d1f', 500)
    s.panel(590, y0, 610, 390, 'How it works', '#0b3a75')
    for i, line in enumerate(how):
        yy = y0 + 92 + i * 56
        s.a(f"<circle cx='630' cy='{yy}' r='17' fill='#0b3a75'/>"); s.t(630, yy + 6, str(i + 1), 17, '#fff', 800, 'middle')
        s.t(660, yy + 6, line, 17, '#1d1d1f', 500)
    s.panel(1230, y0, 510, 390, 'Key features', '#15803d')
    for i, line in enumerate(feats):
        yy = y0 + 92 + i * 48
        s.a(f"<path d='M1258 {yy - 2} l8 9 l16 -18' stroke='#15803d' stroke-width='4' fill='none' stroke-linecap='round' stroke-linejoin='round'/>")
        s.t(1296, yy + 6, line, 17, '#1d1d1f', 500)


def header(s, title, sub):
    s.a(f"<rect width='{W}' height='{H}' fill='#ffffff'/>")
    s.banner(W / 2 - 560, 22, 1120, 64, title, '#0b3a75', 34)
    s.t(W / 2, 112, sub, 21, '#1d1d1f', 600, 'middle')


# ---------------------------------------------------------------- MK1
def mk1():
    s = S()
    header(s, 'MK1 · Working Prototype · Circuit Diagram', '(Arduino Nano + 2× SG90 servos + KY-008 laser + laptop webcam · USB powered)')
    usb = laptop(s, 90, 210, 380)
    phone(s, 180, 690)
    s.a("<path d='M285 700 q60 -60 30 -150' stroke='#f59e0b' stroke-width='3' stroke-dasharray='8 9' fill='none' stroke-linecap='round'/>")
    s.t(330, 640, 'webcam sees the 4 Hz blink', 15, '#92400e', 600, 'start')
    top = ['D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', None, None, None, None]
    bot = [None, None, None, None, None, None, None, None, None, None, '5V', None, 'GND', None, None]
    pins = nano(s, 760, 560, top, bot, 460, 170)
    # USB laptop -> Nano
    s.wire([(usb[0] - 40, usb[1]), (usb[0] + 120, usb[1]), (usb[0] + 120, 645), (734, 645)], COL['usb'], 8)
    s.tag(560, 480, 'USB · data + 5 V power', COL['usb'])
    pan = servo(s, 1200, 200, 'Pan servo')
    tilt = servo(s, 1460, 200, 'Tilt servo')
    las = laser(s, 1440, 975, lab='left')
    # rails (5V red, GND black) below Nano
    RY5, RYG = 870, 905
    s.wire([(pins['5V'][0], pins['5V'][1]), (pins['5V'][0], RY5), (1700, RY5)], COL['5v'])
    s.wire([(pins['GND'][0], pins['GND'][1]), (pins['GND'][0], RYG), (1700, RYG)], COL['gnd'])
    s.tag(pins['5V'][0] - 40, RY5 - 12, '5V', COL['5v'], 'end'); s.tag(pins['GND'][0] + 30, RYG + 32, 'GND', COL['gnd'])
    # servo power + signal (pan lane lower, tilt lane higher: one crossing only)
    for ex, sig, xr, lane in ((pan, 'D9', 1180, 100), (tilt, 'D10', 1440, 76)):
        (bx, by), (rx, ry), (ox, oy) = ex
        s.wire([(bx, by), (bx, by + 40), (xr - 8, by + 40), (xr - 8, RYG)], COL['gnd'], 4.5)
        s.wire([(rx, ry), (rx, ry + 58), (xr + 8, ry + 58), (xr + 8, RY5)], COL['5v'], 4.5)
        px, py = pins[sig]
        s.wire([(ox, oy), (ox, oy + lane), (px, oy + lane), (px, py)], COL['sig'], 4.5)
    s.tag(838, 404, 'Signal · D9 pan · D10 tilt', '#b45309', 'end', 14)
    # laser: S runs up between the servo rails and over the Nano to D7
    lx, ly = pins['D7']
    s.wire([(las['S'][0], las['S'][1]), (las['S'][0], 1115), (1290, 1115), (1290, 470), (lx, 470), (lx, ly)], COL['laser'], 4.5)
    s.tag(1300, 760, 'S → D7', COL['laser'], 'start', 14)
    s.wire([(las['+'][0], las['+'][1]), (las['+'][0], 1080), (1720, 1080), (1720, RY5), (1700, RY5)], COL['5v'], 4.5)
    s.wire([(las['−'][0], las['−'][1]), (las['−'][0], 1100), (1740, 1100), (1740, RYG), (1700, RYG)], COL['gnd'], 4.5)
    panels(s,
           [(COL['5v'], '5 V (VCC)'), (COL['gnd'], 'GND'), (COL['sig'], 'Servo signal (PWM)'), (COL['laser'], 'Laser signal'), (COL['usb'], 'USB (data + power)')],
           ['Webcam sees the phone torch blinking at 4 Hz.', 'ZeroDrift (browser) locks on the blink only.', 'It sends pan / tilt angles over USB serial.', 'Nano moves both servos (D9, D10).', 'Laser on D7 turns on while locked.', 'Everything runs from one USB cable.'],
           ['Identifies the beacon by its blink', 'Ignores steady lights and decoys', 'Laptop webcam, no special sensor', 'Pan + tilt, soft angle limits', 'One USB cable: data and power', 'Tracked a real beacon on camera'],
           [('Arduino Nano (CH340)', '1'), ('SG90 micro servo', '2'), ('Pan-tilt bracket', '1'), ('KY-008 laser module', '1'), ('Laptop with webcam', '1'), ('Mini-USB cable', '1'), ('Jumper wires', 'Set'), ('Phone torch (beacon)', '1')],
           soon=False, final_img='../../docs/media/mk1_photo.jpg', final_title='Working prototype',
           pinmap=[('D9', COL['sig'], 'Pan servo signal'), ('D10', COL['sig'], 'Tilt servo signal'), ('D7', COL['laser'], 'Laser on / off'),
                   ('5V', COL['5v'], 'Servos + laser power'), ('GND', COL['gnd'], 'Common ground'), ('USB', COL['usb'], 'Laptop · serial 115200')])
    return s.svg()


# ---------------------------------------------------------------- MK2
def mk2():
    s = S()
    header(s, 'MK2 · In Development · Circuit Diagram', '(Arduino Nano + 2× A4988 + 2× NEMA 17 + TCA9548A + AS5600 + USB camera + KY-008 laser · 12 V)')
    adp = adapter(s, 60, 170)
    j_in, j_out, sw_in, sw_out = jack_switch(s, 260, 184)
    s.wire([adp, j_in], '#111827', 7)
    s.wire([j_out, sw_in], COL['12v'], 6)
    # 12 V, 5 V and GND buses
    B12, B5, BG = 330, 360, 390
    s.wire([sw_out, (520, sw_out[1]), (520, B12), (1500, B12)], COL['12v'], 6)
    s.tag(560, B12 - 14, '+12 V', COL['12v'])
    s.wire([(300, 240), (300, BG), (1500, BG)], COL['gnd'], 5)
    usb = laptop(s, 60, 470, 300, 'Laptop · ZeroDrift in the browser', cam=False)
    top = ['D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', None, None, None, None]
    bot = [None, None, 'A4', 'A5', None, None, None, None, None, None, '5V', None, 'GND', None, None]
    pins = nano(s, 520, 640, top, bot, 460, 160)
    s.wire([(usb[0] - 40, usb[1]), (usb[0] + 60, usb[1]), (usb[0] + 60, 720), (494, 720)], COL['usb'], 8)
    s.wire([(pins['5V'][0], pins['5V'][1]), (pins['5V'][0], 850), (1010, 850), (1010, B5), (1500, B5)], COL['5v'], 5)
    s.wire([(pins['GND'][0], pins['GND'][1]), (pins['GND'][0], 870), (1032, 870), (1032, BG)], COL['gnd'], 5)
    s.tag(1510, B5 + 6, '+5 V', COL['5v']); s.tag(1510, BG + 30, 'GND', COL['gnd'])
    # drivers + caps + motors
    drv = []
    for k, (dy, nm) in enumerate(((440, 'Pan driver'), (740, 'Tilt driver'))):
        p = a4988(s, 1160, dy, nm)
        drv.append(p)
        # VMOT, GND to buses (right side up)
        vx, vy = p['VMOT']; gx, gy = p['GND']
        s.wire([(vx, vy), (vx + 26, vy), (vx + 26, B12 + 0)], COL['12v'], 4.5)
        s.wire([(gx, gy), (gx + 44, gy), (gx + 44, BG)], COL['gnd'], 4.5)
        cap(s, vx + 88, vy - 34)
        # VDD 5V, logic GND
    for k, p in enumerate(drv):
        mx, my = 1510, (455 if k == 0 else 755)
        ex = nema(s, mx, my, 'Pan motor' if k == 0 else 'Tilt motor', 150)
        for i, nm in enumerate(('2B', '2A', '1A', '1B')):
            px, py = p[nm]; ex_x, ex_y = ex[i]
            col = (COL['c1'], COL['c2'], COL['c3'], COL['c4'])[i]
            midx = 1380 + i * 14
            s.wire([(px, py), (midx, py), (midx, ex_y), (ex_x, ex_y)], col, 4)
    # STEP/DIR from Nano top pins to drivers (left side)
    for k, (st, di) in enumerate((('D2', 'D3'), ('D4', 'D5'))):
        p = drv[k]
        for j, (pin, key, col) in enumerate(((st, 'STEP', COL['step']), (di, 'DIR', COL['dir']))):
            nx, ny = pins[pin]; tx, ty = p[key]
            lane_y = 600 - (k * 2 + j) * 14
            s.wire([(nx, ny), (nx, lane_y), (1090 + (k * 2 + j) * 12, lane_y), (1090 + (k * 2 + j) * 12, ty), (tx, ty)], col, 4)
    s.tag(1000, 546, 'STEP / DIR · D2 D3 (pan) · D4 D5 (tilt)', COL['step'], 'end', 14)
    # I2C: mux (TCA9548A) + AS5600
    mux = small_board(s, 330, 920, 180, 170, 'url(#pcbBlue)', 'TCA9548A', ['VIN', 'GND', 'SDA', 'SCL', 'SD0:left', 'SC0:left'], 'right')
    s.wire([pins['A4'], (pins['A4'][0], 940), (560, 940), (560, mux['SDA'][1]), mux['SDA']], COL['sda'], 4.5)
    s.wire([pins['A5'], (pins['A5'][0], 960), (580, 960), (580, mux['SCL'][1]), mux['SCL']], COL['scl'], 4.5)
    s.tag(335, 905, 'I²C · A4 SDA · A5 SCL', COL['sda'], 'start', 14)
    ams = small_board(s, 80, 930, 170, 120, 'url(#pcbPurple)', 'AS5600', ['SDA', 'SCL', 'VCC', 'GND'], 'right')
    s.wire([mux['SD0'], (316, mux['SD0'][1]), (316, ams['SDA'][1]), ams['SDA']], COL['sda'], 4)
    s.wire([mux['SC0'], (300, mux['SC0'][1]), (300, ams['SCL'][1]), ams['SCL']], COL['scl'], 4)
    s.a("<circle cx='160' cy='975' r='16' fill='#cbd5e1' stroke='#475569' stroke-width='2'/><path d='M160 959 v32' stroke='#dc2626' stroke-width='6'/>")
    s.t(165, 1078, 'pan angle sensor', 13, '#6b7280', 500, 'middle')
    for bd, vp, tx in ((mux, 'VIN', 520), (ams, 'VCC', 262)):
        for nm, col, lab in ((vp, COL['5v'], '5V'), ('GND', COL['gnd'], 'GND')):
            x0, y0 = bd[nm]
            s.wire([(x0, y0), (x0 + 8, y0)], col, 3.5)
            s.t(tx, y0 + 4, lab, 11, col, 800, 'start', MONO)
    # tilt head: camera + laser ride together
    s.a("<rect x='612' y='905' width='404' height='228' rx='18' fill='#f8fafc' stroke='#94a3b8' stroke-width='2' stroke-dasharray='8 7'/>")
    s.t(630, 930, 'TILT HEAD', 13, '#64748b', 800, 'start', MONO)
    usbcam(s, 632, 960)
    lz = laser(s, 800, 1010, 130, 64, lab='above')
    # laser S -> D7: down, right, up the free lane, over the Nano
    dx7, dy7 = pins['D7']
    s.wire([lz['S'], (lz['S'][0], 1118), (1062, 1118), (1062, 618), (dx7, 618), (dx7, dy7)], COL['laser'], 4)
    s.tag(1072, 1004, 'S → D7', COL['laser'], 'start', 13)
    s.t(lz['+'][0], 1100, '5V', 12, COL['5v'], 800, 'middle', MONO)
    s.t(lz['−'][0] + 4, 1100, 'GND', 12, COL['gnd'], 800, 'middle', MONO)
    s.t(1100, 1052, 'MS1–MS3 → 5 V (1/16 step)', 14, '#6b7280', 600, 'start')
    s.t(1100, 1074, 'RST ↔ SLP · EN → GND · VDD → 5 V', 14, '#6b7280', 600, 'start')
    # vibration test motor on D8 (through a 2N2222 transistor)
    vx0, vy0 = vib(s, 1640, 1050)[0]
    s.wire([(vx0, vy0), (vx0 - 56, vy0)], COL['vib'], 4)
    s.tag(vx0 - 62, vy0 + 5, 'D8', COL['vib'], 'end', 13)
    panels(s,
           [(COL['12v'], '+12 V motor power'), (COL['5v'], '+5 V logic'), (COL['gnd'], 'GND'), (COL['step'], 'STEP'), (COL['dir'], 'DIR'), (COL['sda'], 'I²C SDA'), (COL['scl'], 'I²C SCL'), (COL['laser'], 'Laser signal'), (COL['usb'], 'USB')],
           ['USB camera on the tilt head sees the beacon.', 'ZeroDrift locks the 4 Hz blink, rejects decoys.', 'Pan / tilt moves go to the Nano over USB.', 'A4988 drivers step the NEMA 17 motors.', 'AS5600 reads the real pan angle (closed loop).', 'Laser rides with the camera: it hits the target.'],
           ['Camera and laser on one gimbal', 'Smooth 1/16 microstepping', 'Closed loop from the angle sensor', '12 V motors, 5 V logic, kill switch', 'Same software as MK1 and the demo', 'Vibration test built in (D8)'],
           [('Arduino Nano', '1'), ('A4988 stepper driver', '2'), ('NEMA 17 stepper motor', '2'), ('100 µF capacitor', '2'), ('TCA9548A I²C multiplexer', '1'), ('AS5600 angle sensor + magnet', '1'), ('USB camera', '1'), ('KY-008 laser', '1'), ('12 V 2 A adapter + DC jack', '1'), ('Kill switch', '1'), ('Vibration motor + 2N2222', '1')],
           soon=True, final_img='mk2_render.png', final_title='3D design',
           pinmap=[('D2 D3', COL['step'], 'Pan driver STEP / DIR'), ('D4 D5', COL['dir'], 'Tilt driver STEP / DIR'), ('D7', COL['laser'], 'Laser on / off'),
                   ('D8', COL['vib'], 'Vibration test motor'), ('A4 A5', COL['sda'], 'I²C to TCA9548A → AS5600'), ('12V', COL['12v'], 'Motor power (VMOT)'),
                   ('USB', COL['usb'], 'Laptop · serial 115200')])
    return s.svg()


def page(svg):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>"
            "@font-face{font-family:'ZD Inter';src:url(../../docs/fonts/inter-latin-500-normal.woff2);font-weight:500}"
            "@font-face{font-family:'ZD Inter';src:url(../../docs/fonts/inter-latin-600-normal.woff2);font-weight:600}"
            "@font-face{font-family:'ZD Inter';src:url(../../docs/fonts/inter-latin-700-normal.woff2);font-weight:700}"
            "@font-face{font-family:'ZD Inter';src:url(../../docs/fonts/inter-latin-800-normal.woff2);font-weight:800}"
            "html,body{margin:0;background:#fff}svg{display:block}</style></head><body>" + svg + "</body></html>")


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    for name, fn in (('mk1', mk1), ('mk2', mk2)):
        with open(os.path.join(here, f'{name}_infographic.html'), 'w') as f:
            f.write(page(fn()))
    print('ok')
