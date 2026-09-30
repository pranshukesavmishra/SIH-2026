"""Plan Urena: explanatory diagrams (SVG strings), drawn to scale from the CAD numbers."""
import math
from urena_data import P, BELTS

INK, MUTE, GREY, DARK, LINE = '#1d1d1f', '#6e6e73', '#c7ccd3', '#3a3f46', '#8e8e93'
BLUE, ORANGE, GREEN, RED, BRG = '#0a84ff', '#ff9f0a', '#34c759', '#ff3b30', '#e6e9ee'
FONT = "font-family=\"'ZD Inter',Inter,Helvetica,Arial,sans-serif\""


def _svg(w, h, body, title=''):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}" {FONT}>'
            f'<rect width="{w}" height="{h}" fill="#fff"/>{body}</svg>')


def _t(x, y, s, size=13, fill=INK, anchor='start', weight=400):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'


def _lead(x1, y1, x2, y2):
    return f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{LINE}" stroke-width="1"/><circle cx="{x1:.1f}" cy="{y1:.1f}" r="2.2" fill="{LINE}"/>'


# ------------------------------------------------------------------ cable path (front section)
def cable_path():
    S, OX, OY = 1.5, 470.0, 548.0          # px per mm; y=0 at OX; z=0 at OY
    X = lambda y: OX + y * S
    Y = lambda z: OY - z * S
    out = []

    def rect(y0, y1, z0, z1, fill, stroke='none', op=1.0, rx=0, dash=''):
        out.append(f'<rect x="{X(min(y0, y1)):.1f}" y="{Y(max(z0, z1)):.1f}" width="{abs(y1 - y0) * S:.1f}" height="{abs(z1 - z0) * S:.1f}" '
                   f'fill="{fill}" stroke="{stroke}" opacity="{op}" rx="{rx}" {dash}/>')

    def poly(pts, fill, stroke='none'):
        d = ' '.join(f'{X(a):.1f},{Y(b):.1f}' for a, b in pts)
        out.append(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}"/>')

    zt, zm, dr = P['Z_TILT'], P['Z_TILT_MOTOR'], P['DECK_R']
    yl0, yl1 = -P['Y_ARM_OUT'], -P['Y_ARM_IN']             # left arm
    yr0, yr1 = P['Y_ARM_IN_R'], P['Y_ARM_OUT_R']           # right arm
    ye, ys = P['Y_TRUN_END'], P['Y_TSENSOR']
    out.append(f'<path d="M20 {Y(0):.1f} H880" stroke="{LINE}" stroke-width="1.5"/>')
    # base hub walls (section)
    for s_ in (-1, 1):
        pts = [(37, 16 if s_ > 0 else 0), (30, 16 if s_ > 0 else 0), (30, 28), (26, 28), (26, 35), (23, 35), (23, 63), (26, 63), (26, 70), (37, 70)]
        poly([(s_ * a, b) for a, b in pts], GREY)
    for z0 in (28, 63):                                   # 6808 bearings
        for s_ in (-1, 1):
            rect(s_ * 20, s_ * 26, z0, z0 + 7, BRG, INK)
    for s_ in (-1, 1):                                    # spindle, shoulder, pulley, neck, deck, washer
        rect(s_ * 15, s_ * 20, 28.3, 73, '#a7adb5')
        rect(s_ * 20, s_ * 21.5, 70, 73, '#a7adb5')
        rect(s_ * 15, s_ * 27.2, 73, 83, '#9aa0a8')
        rect(s_ * 15, s_ * 24, 83, 100, '#a7adb5')
        rect(s_ * 15, s_ * dr, 100, 107, '#a7adb5')
        rect(s_ * 15.5, s_ * 21.5, 25, 28, '#e0e0e0', INK)
    # tilt motor, its stand and its belt (behind this cut: dashed)
    dash = 'stroke-dasharray="5 4"'
    rect(-15.7, 24.3, zm - 21.15, zm + 21.15, '#2b2e33', op=.85, rx=3)
    rect(24.3, 29.3, 107, zm + 24, '#7d848e')
    rect(36.5, 45.5, zm - 8, zm + 8, '#c9ccd1')
    rect(37.8, 44.2, zm - 7, zt + 26, '#1d1d1f', op=.8)
    # arms with 6806 pockets
    for a0, a1, inner in ((yl1, yl0, yl1), (yr0, yr1, yr0)):
        rect(a0, a1, 107, zt + 27, '#9aa0a8')
        sg = 1 if inner > 0 else -1
        rect(inner + sg * 7, a1, zt - 18, zt + 18, '#fff')
        rect(inner, inner + sg * 7, zt - 21, zt + 21, '#fff')
        for zz in (zt + 15, zt - 21):
            rect(inner, inner + sg * 7, zz, zz + 6, BRG, INK)
    # head
    rect(-32, 32, zt - 29, zt + 29, DARK, rx=6)
    rect(-28.8, 28.8, zt - 25.8, zt + 29.5, '#4a4f57')
    rect(-14, 14, zt - 2, zt + 18, '#1f7a4a')
    # left trunnion (hollow)
    for sg in (-1, 1):
        rect(-32, -36, zt + sg * 10, zt + sg * 23, '#c3c7cd', INK)
        rect(-36, yl1, zt + sg * 10, zt + sg * 17, '#c3c7cd', INK)
        rect(yl1, yl0 - 2, zt + sg * 10, zt + sg * 15, '#c3c7cd', INK)
    # right trunnion: flange + 80T pulley + shoulder + tube, magnet in the end
    for sg in (-1, 1):
        rect(32, 36, zt + sg * 8, zt + sg * 23, '#c3c7cd', INK)
        rect(36, 46, zt + sg * 8, zt + sg * 25.2, '#9aa0a8', INK)
        rect(46, yr0, zt + sg * 8, zt + sg * 17, '#c3c7cd', INK)
        rect(yr0, ye, zt + sg * (8 if sg else 0), zt + sg * 15, '#c3c7cd', INK)
    rect(ye - 4, ye, zt - 8, zt + 8, '#c3c7cd', INK)
    rect(ye - 2.6, ye, zt - 3, zt + 3, RED)
    rect(ys - 1.7, ys, zt - 11.5, zt + 11.5, '#1d6fd1')
    rect(ys, ys + 3.5, zt - 15, zt + 15, '#6f7680')

    # cables
    def path(pts, col, w=3.2):
        d = 'M' + ' L'.join(f'{X(a):.1f} {Y(b):.1f}' for a, b in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>')
    path([(0, zt + 10), (-20, zt), (yl0 - 5, zt), (yl0 - 8, zt - 4), (yl0 - 8, 112), (-6, 112), (-4, 106), (-4, 8), (40, 4), (104, 4)], ORANGE)
    path([(4, zm - 18), (4, 10), (40, 7.5)], BLUE, 2.4)
    path([(ys + 6, zt + 15), (ys + 6, 112), (8, 112), (6, 106)], BLUE, 1.8)
    out.append(_t(X(104) + 6, Y(4) + 4, 'to the electronics box', 12, ORANGE, weight=700))

    L = [((-44, zt + 17), (-150, zt + 58), '6806 bearing (tilt)'),
         ((-48, zt), (-150, zt + 30), 'Left trunnion: Ø20 hole for cables'),
         ((0, zt + 29), (-20, zt + 50), 'Head (camera + laser)'),
         ((-45, 165), (-150, 170), 'Left arm'),
         ((-40, 104), (-150, 108), 'Deck (turns with pan)'),
         ((-23, 66), (-150, 82), '6808 bearings (pan)'),
         ((-17, 45), (-150, 48), 'Hollow spindle, Ø30 hole'),
         ((-18, 26.5), (-150, 18), 'Spindle washer (3 × M3)'),
         ((0, zm), (-150, zm + 12), 'Tilt motor, on the deck (behind)'),
         ((41, zt + 25), (140, zt + 50), '80T pulley, part of the right trunnion'),
         ((ye - 1, zt), (140, zt + 24), 'Magnet in the trunnion end'),
         ((ys - 1, zt - 8), (140, zt - 2), 'Tilt sensor (AS5600)'),
         ((41, 170), (140, 160), f'Tilt belt {BELTS["tilt"]["belt_mm"]:.0f} mm'),
         ((55, 140), (140, 128), 'Right arm'),
         ((27, 78), (140, 86), '80-tooth pan pulley')]
    for (a, b), (c, d), s_ in L:
        x2, y2 = X(c), Y(d)
        out.append(_lead(X(a), Y(b), x2 + (8 if c < 0 else -8), y2 - 4))
        out.append(_t(x2 + (6 if c < 0 else -4), y2, s_, 12.5, INK, 'end' if c < 0 else 'start'))
    out.append(_t(24, 26, 'Where the cables go', 17, INK, weight=700))
    out.append(_t(24, 46, 'Front view, cut through the middle. Orange: camera + laser. Blue: tilt motor + tilt sensor.', 12.5, MUTE))
    out.append(_t(24, 62, 'The tilt motor stands on the deck under the head; everything runs down the hollow pan spindle.', 12.5, MUTE))
    return _svg(900, 560, ''.join(out), 'Cable path through the hollow bearings')


# ------------------------------------------------------------------ belts (top view)
def belts():
    out = []
    S, cx, cy = 3.0, 700.0, 170.0
    C = BELTS['pan']['centre_mm']
    r1, r2 = 80 * 2 / math.pi / 2, 20 * 2 / math.pi / 2
    X = lambda x: cx + x * S
    Y = lambda y: cy - y * S
    ang = math.pi
    phi = math.asin((r1 - r2) / C)
    t = math.pi / 2 + phi
    a1, a2 = ang + t, ang - t
    p1 = [(r1 * math.cos(a), r1 * math.sin(a)) for a in (a1, a2)]
    p2 = [(-C + r2 * math.cos(a), r2 * math.sin(a)) for a in (a1, a2)]
    out.append(f'<circle cx="{X(0)}" cy="{Y(0)}" r="{(r1 + 2) * S}" fill="#e6e9ee" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<circle cx="{X(0)}" cy="{Y(0)}" r="{15 * S}" fill="#fff" stroke="{MUTE}" stroke-dasharray="4 3"/>')
    out.append(f'<circle cx="{X(-C)}" cy="{Y(0)}" r="{(r2 + 2) * S}" fill="#c9ccd1" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<rect x="{X(-C - 21.15)}" y="{Y(21.15)}" width="{42.3 * S}" height="{42.3 * S}" rx="10" fill="none" stroke="{MUTE}" stroke-dasharray="5 4"/>')
    big = f'M{X(p1[0][0]):.1f} {Y(p1[0][1]):.1f} A{r1 * S:.1f} {r1 * S:.1f} 0 1 1 {X(p1[1][0]):.1f} {Y(p1[1][1]):.1f}'
    out.append(f'<path d="{big} L{X(p2[1][0]):.1f} {Y(p2[1][1]):.1f} A{r2 * S:.1f} {r2 * S:.1f} 0 0 1 {X(p2[0][0]):.1f} {Y(p2[0][1]):.1f} Z" fill="none" stroke="{INK}" stroke-width="4"/>')
    # slide arrows
    y0 = Y(-30)
    out.append(f'<path d="M{X(-C - 7):.1f} {y0} H{X(-C + 3):.1f}" stroke="{BLUE}" stroke-width="2.5"/>'
               f'<path d="M{X(-C - 7):.1f} {y0 - 6} v12 M{X(-C + 3):.1f} {y0 - 6} v12" stroke="{BLUE}" stroke-width="2.5"/>')
    out.append(_t(X(-C - 2), y0 + 22, 'motor slides 7 mm out / 3 mm in', 12.5, BLUE, 'middle', 700))
    out.append(_t(X(-C - 2), y0 + 38, 'to tighten the belt', 12.5, BLUE, 'middle'))
    out.append(_t(X(0), Y(0) - 4, '80 teeth', 15, INK, 'middle', 700))
    out.append(_t(X(0), Y(0) + 14, 'Ø30 cable hole', 11.5, MUTE, 'middle'))
    out.append(_t(X(-C), Y(r2 + 5) - 6, '20 teeth', 13, INK, 'middle', 700))
    out.append(_t(X(-C), Y(24) - 6, 'pan motor', 12, MUTE, 'middle'))
    out.append(f'<path d="M{X(-C):.1f} {Y(-56)} H{X(0):.1f}" stroke="{MUTE}" stroke-width="1"/>'
               f'<path d="M{X(-C):.1f} {Y(-56) - 5} v10 M{X(0):.1f} {Y(-56) - 5} v10" stroke="{MUTE}"/>')
    out.append(_t(X(-C / 2), Y(-56) + 18, f'{C:.1f} mm between centres', 12.5, MUTE, 'middle'))
    # text block
    out.append(_t(24, 34, 'The belts: 4 motor turns = 1 axis turn', 17, INK, weight=700))
    fits_p = BELTS['pan']['belts_that_fit_mm']
    fits_t = BELTS['tilt']['belts_that_fit_mm']
    lines = [f'Pan belt: {BELTS["pan"]["belt_mm"]:.0f} mm closed GT2, 6 mm wide',
             f'(any {fits_p[0]}–{fits_p[-1]} mm fits, so 240 mm is fine too)',
             f'Tilt belt: {BELTS["tilt"]["belt_mm"]:.0f} mm closed GT2 ({fits_t[0]}–{fits_t[-1]} mm fits)',
             '',
             '4:1 means 4 × the torque and 4 × finer steps:',
             f'{BELTS["steps_per_output_deg"]:.1f} motor steps per degree of the rig.',
             'Metal 20T pulleys on the motors, printed 80T on the axes.']
    for i, s in enumerate(lines):
        out.append(_t(24, 64 + i * 20, s, 13, INK if i != 1 and i != 5 else MUTE))
    return _svg(900, 370, ''.join(out), 'Belt drive, top view')


# ------------------------------------------------------------------ pen drive for the print shop
def pendrive():
    out = [f'<rect x="30" y="70" width="170" height="74" rx="14" fill="#2b2f36"/>',
           f'<rect x="200" y="86" width="44" height="42" rx="4" fill="#c7c7cc" stroke="{LINE}"/>',
           f'<rect x="212" y="98" width="8" height="8" fill="{LINE}"/><rect x="226" y="98" width="8" height="8" fill="{LINE}"/>',
           _t(115, 104, 'PEN DRIVE', 15, '#fff', 'middle', 700), _t(115, 124, '(or a zip on WhatsApp)', 11.5, '#c7ccd3', 'middle'),
           f'<path d="M250 107 H300" stroke="{INK}" stroke-width="2" marker-end="url(#pa)"/>',
           '<defs><marker id="pa" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1d1d1f"/></marker></defs>']
    tree = [('PlanUrena_print/', 0, True, ''), ('1_PRINT_FIRST/', 1, True, ''), ('00_test_coupon.stl', 2, False, 'print, then we check it'),
            ('2_STL/', 1, True, ''), ('01_base_hub.stl … (20 files)', 2, False, 'already turned the right way up'),
            ('3_STEP/', 1, True, ''), ('same parts as STEP', 2, False, 'only if they want to edit'),
            ('Plan_Urena_print_shop.pdf', 1, False, 'settings + parts list'), ('README.txt', 1, False, 'the same, short')]
    y = 40
    for s, lvl, folder, note in tree:
        x = 320 + lvl * 24
        icon = (f'<path d="M{x} {y - 11} h7 l3 3 h10 v12 h-20 z" fill="#ffd60a" stroke="#b58900"/>' if folder else
                f'<path d="M{x + 2} {y - 12} h11 l5 5 v13 h-16 z" fill="#fff" stroke="{LINE}"/>')
        out.append(icon + _t(x + 28, y, s, 13.5, INK, weight=700 if folder else 400))
        if note:
            out.append(_t(760, y, note, 12, MUTE, 'end'))
        y += 22
    return _svg(780, 236, ''.join(out), 'What to give the print shop')


# ------------------------------------------------------------------ camera field of view
def camera_fov():
    from urena_data import CAMERAS
    out = [_t(24, 30, 'Narrower view = finer aim', 17, INK, weight=700),
           _t(24, 50, 'The tracker aims to about one pixel, so degrees per pixel sets the accuracy.', 12.5, MUTE)]
    y = 110
    for name, price, fov_s, fov, px, why, kind in CAMERAS:
        if not px:
            continue
        col = GREEN if kind == 'best' else BLUE
        h = math.tan(math.radians(fov / 2)) * 70
        out.append(f'<path d="M60 {y} L130 {y - h:.1f} L130 {y + h:.1f} Z" fill="{col}" opacity=".18" stroke="{col}"/>')
        out.append(f'<circle cx="60" cy="{y}" r="6" fill="{INK}"/>')
        out.append(_t(170, y - 8, name.split(' (')[0].split(' + ')[0], 13.5, INK, weight=700))
        out.append(_t(170, y + 12, f'{fov_s} → {fov / px:.3f}° per pixel', 12.5, col if kind == 'best' else MUTE, weight=700 if kind == 'best' else 400))
        y += 112
    return _svg(640, y - 40, ''.join(out), 'Camera field of view comparison')
