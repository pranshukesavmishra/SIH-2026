"""Plan Urena · ZeroDrift MK3 pan-tilt terminal — parametric CAD (CadQuery).

One source for every printed part. Run:

    python3 tools/mk3/mk3_cad.py            # STEP + STL for every part, assembly meshes, report

Outputs
    tools/mk3/out/print/*.stl   parts to 3D print (each in its print orientation, on Z=0)
    tools/mk3/out/step/*.step   same parts as STEP (for the print shop / edits)
    docs/mk3/models/*.stl       every part, bought or printed, placed in the assembly (for the 3D viewer)
    tools/mk3/out/report.json   belt maths, masses, clearances, print estimates

Units: millimetres. Z is up; the pan axis is the Z axis; at zero pan the head looks along +X;
the tilt axis is parallel to Y.

Every fit-critical number is in the PARAMETERS block. Print the test coupon first
(tools/mk3/out/print/00_test_coupon.stl) and adjust HOLE_CLEAR / BRG_PRESS if a fit is off.
"""
import json, math, os
import cadquery as cq

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..'))
OUT = os.path.join(ROOT, 'out')
PRINT_DIR, STEP_DIR = os.path.join(OUT, 'print'), os.path.join(OUT, 'step')
VIEW_DIR = os.path.join(REPO, 'docs', 'mk3', 'models')
for d in (PRINT_DIR, STEP_DIR, VIEW_DIR):
    os.makedirs(d, exist_ok=True)

# ============================================================== PARAMETERS
HOLE_CLEAR = 0.25          # printed holes come out small: add this to every bore/slot
# Hollow bearings (like the reference build): stiff, and the cables run through the middle.
PAN_BRG = (52.0, 40.0, 7.0)            # 6808-2RS: OD, bore, width
TILT_BRG = (42.0, 30.0, 7.0)           # 6806-2RS
BRG_PRESS = 0.10           # bearing pockets = OD + 0.10: light press fit (tune with the coupon)
RACE_FIT = 0.05            # printed spindle / trunnion OD = bearing bore - this (slide fit)
NEMA, NEMA_HOLES, NEMA_PILOT, NEMA_LEN = 42.3, 31.0, 22.0, 40.0  # NEMA17, 40 mm body
NEMA_SHAFT, NEMA_SHAFT_LEN = 5.0, 24.0
M3, M3_NUT_AF, M3_HEAD = 3.2, 5.7, 5.8  # clearance, nut across-flats (+clearance), head dia
M4, M4_NUT_AF = 4.3, 7.2
GT2_PITCH, BELT_W = 2.0, 6.0
T_SMALL, T_BIG = 20, 80    # 20T metal pulley on each motor, 80T on each axis -> 4:1
PD_SMALL = T_SMALL * GT2_PITCH / math.pi   # 12.73 pitch diameter
PD_BIG = T_BIG * GT2_PITCH / math.pi       # 50.93
BELT_PAN_L, BELT_TILT_L = 232.0, 280.0     # standard closed-loop GT2-6mm lengths
PAN_SLIDE_IN, PAN_SLIDE_OUT = 3.0, 7.0     # pan motor travel: takes a 227..245 mm belt (232 or 240 both fit)
WALL = 3.2
MAG_D, MAG_T = 6.0, 2.5    # diametric magnet that comes with the AS5600 board

# heights (Z) of the pan stack
Z_HUB_TOP = 70.0            # top of the base hub = top face of the upper pan bearing
Z_BRG_LOW = 28.0            # bottom face of the lower pan bearing
PAN_CAVITY_R = 30.0         # open cavity under the lower bearing (washer + cables)
Z_BELT_PAN = 78.0           # centre plane of the pan belt
Z_PAN_PLATE = 62.0          # pan motor flange (underside of the 4 mm motor plate, top at 66)
Z_DECK_BOT, DECK_T = 100.0, 7.0
Z_DECK_TOP = Z_DECK_BOT + DECK_T
DECK_R = 70.0
Z_TILT = Z_DECK_TOP + 105.0 # tilt axis height (212): the head swings clear above the tilt motor
SPINDLE_BORE_R = 15.0       # 30 mm cable hole down the pan axis
ARM_T = 12.0                # yoke arm thickness (Y)
HEAD_W = 64.0               # head width (Y)
ARM_GAP = 7.0               # head side -> left arm: trunnion flange (4) + shoulder (3)
Y_ARM_IN = HEAD_W / 2 + ARM_GAP          # inner face of the LEFT arm (39)
Y_ARM_OUT = Y_ARM_IN + ARM_T             # 51
ARM_BOSS_R = 27.0
# Right side: the tilt pulley is part of the right trunnion and runs INSIDE, between the
# head and the right arm; the tilt motor stands on the deck under the head.
Y_PUL0 = HEAD_W / 2 + 4.0                # pulley starts right after the trunnion flange (36)
Y_BELT_TILT = Y_PUL0 + 1.5 + (BELT_W + 1) / 2     # belt centre plane (41)
Y_ARM_IN_R = Y_PUL0 + 1.5 + BELT_W + 1 + 1.5 + 3.0   # right arm inner face, after a 3 mm shoulder (49)
Y_ARM_OUT_R = Y_ARM_IN_R + ARM_T         # 61
Y_TRUN_END = Y_ARM_OUT_R + 2.0           # right trunnion end: the tilt magnet sits in it (63)
Y_TSENSOR = Y_TRUN_END + 1.5 + 1.0 + 1.6 + 0.1   # tilt sensor bracket plate inner face (67.2)
TILT_MOTOR_X = -35.0                     # tilt motor sits behind the axis: the cable hole stays free
TILT_SLIDE = 2.5                         # tilt motor slides +/- this (vertically) to tension its belt
Y_TPLATE = Y_BELT_TILT - 4.5 - 7.0 - 0.2 - 5.0   # tilt motor plate, -Y face (motor flange side) (24.3)
TRUN_BORE_L, TRUN_BORE_R = 10.0, 8.0     # left trunnion: 20 mm cable hole; right: lightening bore
TRUN_BOLT_R = 18.5
HEAD_L, HEAD_H = 92.0, 58.0              # head length (X) and height (Z)

# ============================================================== belt maths
def belt_center_distance(L, t1, t2, p=GT2_PITCH):
    """Exact centre distance for a closed belt of pitch length L on t1/t2 tooth pulleys."""
    r1, r2 = t1 * p / (2 * math.pi), t2 * p / (2 * math.pi)
    lo, hi = abs(r2 - r1) + 1e-6, L
    for _ in range(200):
        C = (lo + hi) / 2
        phi = math.asin((r2 - r1) / C)
        Lc = 2 * C * math.cos(phi) + math.pi * (r1 + r2) + 2 * phi * (r2 - r1)
        lo, hi = (C, hi) if Lc < L else (lo, C)
    return C

C_PAN = belt_center_distance(BELT_PAN_L, T_SMALL, T_BIG)
C_TILT = belt_center_distance(BELT_TILT_L, T_SMALL, T_BIG)
Z_TILT_MOTOR = Z_TILT - math.sqrt(C_TILT ** 2 - TILT_MOTOR_X ** 2)
X_PAN_MOTOR = -C_PAN

# ============================================================== helpers
def cyl(r, h, z0=0.0, x=0.0, y=0.0):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(r).extrude(h)

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def ycyl(r, y0, y1, x=0.0, z=0.0):
    """cylinder along Y from y0 to y1"""
    return cq.Workplane('XZ').workplane(offset=-y1).center(x, z).circle(r).extrude(y1 - y0)

def xcyl(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane('YZ').workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)

def hexnut_pocket_z(x, y, z0, depth, af=M3_NUT_AF):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).polygon(6, af / math.cos(math.pi / 6)).extrude(depth)

def ring(r_out, r_in, h, z0=0.0):
    return cyl(r_out, h, z0).cut(cyl(r_in, h + 2, z0 - 1))

def gt2_pulley(teeth, width, flange=1.5, flange_extra=2.0):
    """GT2 toothed rim along Z, bottom flange at z=0, teeth, top flange. Returns (solid, height)."""
    pd = teeth * GT2_PITCH / math.pi
    od = pd - 0.508
    tooth_w = width + 1.0
    rim = cyl(od / 2, tooth_w, flange)
    groove = (cq.Workplane('XY').workplane(offset=flange - 0.1)
              .polarArray(od / 2, 0, 360, teeth).circle(0.555).extrude(tooth_w + 0.2))
    rim = rim.cut(groove)
    f1 = cyl(od / 2 + flange_extra, flange, 0)
    f2 = cyl(od / 2 + flange_extra, flange, flange + tooth_w)
    return f1.union(rim).union(f2), 2 * flange + tooth_w

def polar(n, r, a0=90.0):
    return [(r * math.cos(math.radians(a0 + i * 360 / n)), r * math.sin(math.radians(a0 + i * 360 / n))) for i in range(n)]

# ============================================================== PRINTED PARTS (assembly frame)
PARTS = {}      # name -> dict(shape, group, colour, printed, qty, print_rot)

def add(name, shape, group, colour, printed=True, qty=1, print_rot=None, note=''):
    PARTS[name] = dict(shape=shape, group=group, colour=colour, printed=printed, qty=qty, print_rot=print_rot, note=note)

PB_OD, PB_ID, PB_W = PAN_BRG
TB_OD, TB_ID, TB_W = TILT_BRG

# ---------- 01 base hub: two 6808 pockets, open centre, pan motor tower, leg sockets
def base_hub():
    hub = cyl(37, Z_HUB_TOP, 0)
    mx = X_PAN_MOTOR
    zp = Z_PAN_PLATE
    tower = box(mx - 27 - PAN_SLIDE_OUT, mx + 27, -27, 27, 12, zp + 4)
    web = box(mx + 10, -20, -22, 22, 12, zp + 4)
    body = hub.union(tower).union(web)
    # motor pocket (motor hangs below its 4 mm plate; open at the bottom for its cable)
    body = body.cut(box(mx - NEMA / 2 - 0.6 - PAN_SLIDE_OUT, mx + NEMA / 2 + 0.6 + PAN_SLIDE_IN, -NEMA / 2 - 0.6, NEMA / 2 + 0.6, 11, zp))
    body = body.cut(box(mx - 12, mx + 12, -30, -18, 11, 40))        # motor cable exit
    # slotted pilot and screw holes: motor slides 3 mm in / 7 mm out along X to tension the belt
    sc, sl = mx - (PAN_SLIDE_OUT - PAN_SLIDE_IN) / 2, PAN_SLIDE_OUT + PAN_SLIDE_IN
    body = body.cut(cq.Workplane('XY').workplane(offset=zp - 1).center(sc, 0).slot2D(NEMA_PILOT + 1.0 + sl, NEMA_PILOT + 1.0, 0).extrude(6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(cq.Workplane('XY').workplane(offset=zp - 1).center(sc + sx * NEMA_HOLES / 2, sy * NEMA_HOLES / 2)
                            .slot2D(M3 + sl, M3, 0).extrude(6))
    # pan bearings: upper pocket from the top, lower pocket opened from below, a step between
    # them that touches only the OUTER races (bore 46 < outer-race inner edge 48.5)
    body = body.cut(cyl(23.0, Z_HUB_TOP + 1, -0.5))
    body = body.cut(cyl((PB_OD + BRG_PRESS) / 2, PB_W + 0.2, Z_HUB_TOP - PB_W))
    body = body.cut(cyl((PB_OD + BRG_PRESS) / 2, PB_W, Z_BRG_LOW))
    body = body.cut(cyl(PAN_CAVITY_R, Z_BRG_LOW + 0.5, -0.5))       # washer + cable turn-out
    # cable exit at 60 deg, between two legs
    body = body.cut(box(0, 60, -12, 12, -0.5, 16).rotate((0, 0, 0), (0, 0, 1), CABLE_EXIT_DEG))
    for a in LEG_DEG:
        body = body.union(leg_socket(a))
    for a in LEG_DEG:                                              # tongue slot runs into the hub wall too
        body = body.cut(box(34, 60, -9.2, 9.2, 4, 22.2).rotate((0, 0, 0), (0, 0, 1), a))
    return body

def leg_socket(a_deg):
    s = box(30, 58, -13, 13, 0, 26)
    s = s.cut(box(34, 60, -9.2, 9.2, 4, 22.2))                      # leg tongue 18 wide, 18 tall
    for x in (41, 51):
        s = s.cut(cq.Workplane('XY').center(x, 0).circle(M4 / 2).extrude(30))
        s = s.cut(hexnut_pocket_z(x, 0, -0.1, 4.0, M4_NUT_AF))
    return s.rotate((0, 0, 0), (0, 0, 1), a_deg)

# ---------- 02 leg x3 (printed on its side)
LEG_LEN = 150.0
LEG_DEG = (0, 120, 240)        # 60 deg clear of the pan motor tower at 180
CABLE_EXIT_DEG = 60
def leg(a_deg=90):
    tongue = box(34, 58, -9, 9, 4.2, 22)
    beam = (cq.Workplane('XZ').polyline([(58, 0), (58, 26), (LEG_LEN + 30, 12), (LEG_LEN + 30, 0)]).close()
            .extrude(9).translate((0, 9, 0)))
    beam = beam.union(beam.mirror('XZ'))
    beam = beam.cut(box(80, LEG_LEN + 10, -5, 5, 4, 12))            # lightening slot keeps an I-section
    foot = cyl(16, 4, 0, LEG_LEN + 28, 0)
    part = tongue.union(beam).union(foot)
    for x in (41, 51):
        part = part.cut(cq.Workplane('XY').center(x, 0).circle(M4 / 2).extrude(30))
    part = part.cut(cyl(3.1, 10, -0.1, LEG_LEN + 28, 0))            # hole for an M6 levelling foot (optional)
    return part.rotate((0, 0, 0), (0, 0, 1), a_deg)

# ---------- pan motor stack: pulley hub down, magnet cap on the shaft tip, sensor bridge above
PAN_PUL20_Z = Z_BELT_PAN                          # 20T teeth centred on the belt
PAN_SHAFT_TOP = Z_PAN_PLATE + NEMA_SHAFT_LEN      # 86
PAN_CAP_Z0 = PAN_PUL20_Z + 4.5 + 0.5              # cap starts 0.5 above the pulley's top flange
PAN_CAP_H = 6.0
PAN_MAG_TOP = PAN_CAP_Z0 + PAN_CAP_H              # magnet face (89)
PAN_BOARD_Z = PAN_MAG_TOP + 1.5 + 1.0             # AS5600 board underside (chip faces down)
PAN_BRIDGE_Z = PAN_BOARD_Z + 1.6 + 0.1            # bridge plate underside

# ---------- 03 pan sensor bridge: rides on the two rear motor screws, so it slides with the motor
def pan_sensor_bridge():
    mx = X_PAN_MOTOR
    z0, z1 = Z_PAN_PLATE + 4, PAN_BRIDGE_Z
    b = box(mx - 21, mx + 14, -21, 21, z1, z1 + 4)
    for sy in (-1, 1):
        b = b.union(cyl(4.6, z1 - z0, z0, mx - NEMA_HOLES / 2, sy * NEMA_HOLES / 2))
        b = b.union(box(mx - 21, mx - 11, sy * NEMA_HOLES / 2 - 4.6, sy * NEMA_HOLES / 2 + 4.6, z1 - 6, z1))   # web
        b = b.cut(cyl(M3 / 2, 60, z0 - 1, mx - NEMA_HOLES / 2, sy * NEMA_HOLES / 2))
        b = b.cut(cyl(M3_HEAD / 2 + 0.3, 3, z1 + 2, mx - NEMA_HOLES / 2, sy * NEMA_HOLES / 2))   # head counterbore
    for x in (-7.75, 7.75):                                        # AS5600 board, 2 x M2.5 from below
        b = b.cut(cyl(1.1, 10, z1 - 1, mx + x, 7.9))
    b = b.cut(box(mx + 4, mx + 15, -6, 6, z1 - 1, z1 + 5))          # wire slot for the header
    return b

# ---------- 04 magnet cap: centres the magnet on the 5 mm pan motor shaft tip
def magnet_cap():
    c = cyl(5.0, PAN_CAP_H, 0)
    c = c.cut(cyl(NEMA_SHAFT / 2 + 0.05, 3.0 + 0.1, -0.1))         # 3 mm onto the shaft (+ a drop of glue)
    c = c.cut(cyl(MAG_D / 2 + 0.1, MAG_T + 0.1, PAN_CAP_H - MAG_T))
    return c

# ---------- 05 spindle washer: 3 x M3 into the spindle end, preloads the lower bearing
SPINDLE_Z0 = Z_BRG_LOW + 0.3        # spindle stops 0.3 above the bearing face so the washer bears on the race
def spindle_washer():
    w = ring(PB_ID / 2 + 1.5, SPINDLE_BORE_R + 0.5, 3.0, Z_BRG_LOW - 3.0)
    for (x, y) in polar(3, 17.5):
        w = w.cut(cyl(M3 / 2, 10, Z_BRG_LOW - 5, x, y))
    return w

# ---------- 06 pan turntable: hollow spindle + 80T pulley + deck, one print (deck down)
def pan_turntable():
    pul, ph = gt2_pulley(T_BIG, BELT_W)
    z_pul0 = Z_BELT_PAN - (BELT_W + 1) / 2 - 1.5
    pul = pul.translate((0, 0, z_pul0))
    spindle = cyl(PB_ID / 2 - RACE_FIT / 2, z_pul0 - SPINDLE_Z0 + 0.5, SPINDLE_Z0)
    shoulder = cyl(PB_ID / 2 + 1.5, z_pul0 - Z_HUB_TOP + 0.5, Z_HUB_TOP)        # presses the upper INNER race
    neck = cyl(24, Z_DECK_BOT - (z_pul0 + ph) + 0.5, z_pul0 + ph - 0.2)
    deck = cyl(DECK_R, DECK_T, Z_DECK_BOT)
    part = spindle.union(shoulder).union(pul).union(neck).union(deck)
    part = part.cut(cyl(SPINDLE_BORE_R, 200, SPINDLE_Z0 - 1))                    # cable hole
    for a in (0, 180):                                                           # lightening windows
        part = part.cut(cq.Workplane('XY').workplane(offset=Z_DECK_BOT - 1).transformed(rotate=(0, 0, a))
                        .center(40, 0).slot2D(26, 14, 90).extrude(DECK_T + 2))
    for (x, y) in polar(3, 17.5):                                                # washer screws (self-tap)
        part = part.cut(cyl(M3 / 2 * 0.86, 12, SPINDLE_Z0 - 1, x, y))
    for yc in (-(Y_ARM_IN + ARM_T / 2), Y_ARM_IN_R + ARM_T / 2):               # arm bolts, nut traps below
        for x in (-26, -8, 8, 26):
            y = yc
            part = part.cut(cyl(M4 / 2, DECK_T + 2, Z_DECK_BOT - 1, x, y))
            part = part.cut(hexnut_pocket_z(x, y, Z_DECK_BOT - 0.1, 3.6, M4_NUT_AF))
    for x in TPLATE_BOLTS_X:                                                    # tilt motor plate bolts
        part = part.cut(cyl(M4 / 2, DECK_T + 2, Z_DECK_BOT - 1, x, TPLATE_BOLT_Y))
        part = part.cut(hexnut_pocket_z(x, TPLATE_BOLT_Y, Z_DECK_BOT - 0.1, 3.6, M4_NUT_AF))
    return part, z_pul0, ph

TPLATE_BOLTS_X = (TILT_MOTOR_X - 22, TILT_MOTOR_X + 22)
TPLATE_BOLT_Y = Y_TPLATE + 5.0 + 6.0

# ---------- 07/08 yoke arms: 6806 pocket from the inner face, lip on the outer face
ARM_L = 80.0
def arm(side):
    """side = +1 (right: tilt pulley side, sensor outside) or -1 (left: cable side)."""
    y0, y1 = (Y_ARM_IN_R, Y_ARM_OUT_R) if side > 0 else (-Y_ARM_OUT, -Y_ARM_IN)
    prof = (cq.Workplane('XZ').polyline([(-ARM_L / 2, Z_DECK_TOP), (ARM_L / 2, Z_DECK_TOP),
                                         (ARM_BOSS_R, Z_TILT - 4), (-ARM_BOSS_R, Z_TILT - 4)]).close()
            .extrude(-(y1 - y0)).translate((0, y0, 0)))
    a = prof.union(ycyl(ARM_BOSS_R, y0, y1, 0, Z_TILT)).union(box(-ARM_L / 2, ARM_L / 2, y0, y1, Z_DECK_TOP, Z_DECK_TOP + 10))
    inner = y0 if side > 0 else y1
    pocket = ycyl((TB_OD + BRG_PRESS) / 2, inner - 1, inner + TB_W, 0, Z_TILT) if side > 0 else \
             ycyl((TB_OD + BRG_PRESS) / 2, inner - TB_W, inner + 1, 0, Z_TILT)
    a = a.cut(pocket)
    a = a.cut(ycyl(18.0, y0 - 1, y1 + 1, 0, Z_TILT))          # lip: touches only the outer race
    for x in (-26, -8, 8, 26):                               # bolt slots into the deck (+/-1.5 mm in Y)
        a = a.cut(cq.Workplane('XY').workplane(offset=Z_DECK_TOP - 1).center(x, (y0 + y1) / 2).slot2D(M4 + 3, M4, 90).extrude(30))
        a = a.cut(cq.Workplane('XY').workplane(offset=Z_DECK_TOP + 10).center(x, (y0 + y1) / 2).slot2D(8.4 + 3, 8.4, 90).extrude(40))
    for zc in (Z_DECK_TOP + 36, Z_DECK_TOP + 70):            # two lightening windows (taller arm)
        a = a.cut(cq.Workplane('XZ').workplane(offset=-y1 - 1).center(0, zc).slot2D(24, 13, 90).extrude(y1 - y0 + 2))
    if side > 0:
        # relief for the tilt motor's shaft tip (it slides +/- TILT_SLIDE)
        a = a.cut(cq.Workplane('XZ').workplane(offset=-(y0 + 3)).center(TILT_MOTOR_X, Z_TILT_MOTOR).slot2D(12 + 2 * TILT_SLIDE, 12, 90).extrude(4))
        for x in (-23.5, 23.5):                              # tilt sensor bracket screws (self-tap)
            a = a.cut(ycyl(M3 / 2 * 0.86, y1 - 10, y1 + 1, x, Z_TILT))
    return a

# ---------- 09 tilt motor plate: stands on the deck, motor on its back, slotted to tension the belt
def tilt_motor_plate():
    x0, x1 = TILT_MOTOR_X - 31, TILT_MOTOR_X + 31
    y0, y1 = Y_TPLATE, Y_TPLATE + 5.0
    ztop = Z_TILT_MOTOR + 21.5 + TILT_SLIDE
    p = box(x0, x1, y0, y1, Z_DECK_TOP, ztop)
    p = p.union(box(x0, x1, y1 - 0.01, y1 + 12, Z_DECK_TOP, Z_DECK_TOP + 5))              # foot on the deck
    for x in (x0 + 3, x1 - 3):                                                            # gussets
        p = p.union(cq.Workplane('YZ').workplane(offset=x - 1.5).polyline([(y1 - 0.01, Z_DECK_TOP), (y1 + 12, Z_DECK_TOP), (y1 - 0.01, Z_DECK_TOP + 22)]).close().extrude(3))
    for x in TPLATE_BOLTS_X:
        p = p.cut(cyl(M4 / 2, 8, Z_DECK_TOP - 1, x, TPLATE_BOLT_Y))
    p = p.cut(cq.Workplane('XZ').workplane(offset=-(y1 + 1)).center(TILT_MOTOR_X, Z_TILT_MOTOR).slot2D(NEMA_PILOT + 1 + 2 * TILT_SLIDE, NEMA_PILOT + 1, 90).extrude(7))
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = p.cut(cq.Workplane('XZ').workplane(offset=-(y1 + 1)).center(TILT_MOTOR_X + sx * NEMA_HOLES / 2, Z_TILT_MOTOR + sz * NEMA_HOLES / 2)
                      .slot2D(M3 + 2 * TILT_SLIDE, M3, 90).extrude(7))
    return p

# ---------- 10 tilt sensor bracket: outside the right arm, holds the AS5600 facing the trunnion end
def tilt_sensor_bracket():
    ya, yb = Y_ARM_OUT_R, Y_TSENSOR
    b = box(-27, 27, yb, yb + 3.5, Z_TILT - 15, Z_TILT + 15)
    for sx in (-1, 1):
        leg = box(min(sx * 20.5, sx * 26.5), max(sx * 20.5, sx * 26.5), ya, yb + 0.01, Z_TILT - 6, Z_TILT + 6)
        b = b.union(leg).cut(ycyl(M3 / 2, ya - 1, yb + 5, sx * 23.5, Z_TILT))
        b = b.cut(ycyl(M3_HEAD / 2 + 0.3, yb + 1.5, yb + 5, sx * 23.5, Z_TILT))
    for x in (-7.75, 7.75):                                  # AS5600 board, 2 x M2.5 from the inside
        b = b.cut(ycyl(1.1, yb - 1, yb + 5, x, Z_TILT + 7.9))
    b = b.cut(box(-6, 6, yb - 1, yb + 5, Z_TILT + 11, Z_TILT + 16))    # header wires out the top
    return b

# ---------- 11 head (optics bench) + 12 front plate + 13 laser holder
CAM_Y, LASER_Y, OPT_Z = -15.0, 16.0, 8.0
def head():
    x0, x1 = -HEAD_L / 2, HEAD_L / 2
    y0, y1 = -HEAD_W / 2, HEAD_W / 2
    z0, z1 = Z_TILT - HEAD_H / 2, Z_TILT + HEAD_H / 2
    h = box(x0, x1, y0, y1, z0, z1).edges('|X').fillet(6)
    h = h.cut(box(x0 + WALL, x1 - 8, y0 + WALL, y1 - WALL, z0 + WALL, z1 + 1))   # open top: easy wiring
    # trunnion seats: 2 mm pads inside each side wall, 3 x M3 through
    for s in (-1, 1):
        yw = s * (HEAD_W / 2 - WALL)
        h = h.union(ycyl(23, min(yw, yw - s * 2), max(yw, yw - s * 2), 0, Z_TILT))
        for (x, z) in polar(3, TRUN_BOLT_R):
            h = h.cut(ycyl(M3 / 2, y0 - 1, y1 + 1, x, Z_TILT + z))
    h = h.cut(ycyl(TRUN_BORE_L + 0.5, y0 - 1, y0 + 8, 0, Z_TILT))          # cables out through the left trunnion
    # front face: camera window + laser bore through the 8 mm front wall
    h = h.cut(xcyl(9.5, x1 - 9, x1 + 1, CAM_Y, Z_TILT + OPT_Z))
    h = h.cut(xcyl(8.0, x1 - 9, x1 + 1, LASER_Y, Z_TILT + OPT_Z))
    for (y, z) in ((CAM_Y - 16, Z_TILT + OPT_Z - 20), (CAM_Y + 16, Z_TILT + OPT_Z - 20), (LASER_Y + 14, Z_TILT + OPT_Z - 20)):
        h = h.cut(xcyl(M3 / 2 * 0.86, x1 - 9, x1 + 1, y, z))
    return h

def front_plate():
    """camera board (slots fit 28-34 mm hole patterns) + laser holder seat; bolts to the head front."""
    x1 = HEAD_L / 2
    p = box(x1, x1 + 4, -HEAD_W / 2, HEAD_W / 2, Z_TILT + OPT_Z - 26, Z_TILT + OPT_Z + 22)
    p = p.edges('|X').fillet(3)
    p = p.cut(xcyl(8.5, x1 - 1, x1 + 6, CAM_Y, Z_TILT + OPT_Z))
    p = p.cut(xcyl(6.25, x1 - 1, x1 + 6, LASER_Y, Z_TILT + OPT_Z))
    for (y, z) in ((CAM_Y - 16, Z_TILT + OPT_Z - 20), (CAM_Y + 16, Z_TILT + OPT_Z - 20), (LASER_Y + 14, Z_TILT + OPT_Z - 20)):
        p = p.cut(xcyl(M3 / 2, x1 - 1, x1 + 6, y, z))
    for sy in (-1, 1):
        for sz in (-1, 1):
            p = p.cut(cq.Workplane('YZ').workplane(offset=x1 - 1).center(CAM_Y + sy * 15.5, Z_TILT + OPT_Z + sz * 15.5)
                      .slot2D(6.0 + 2.4, 2.4, 45 if sy * sz > 0 else -45).extrude(6))
    return p

def laser_holder():
    """tube for a 12 mm laser module, 3 M3 push screws at 120 deg to boresight it on the camera"""
    x1 = HEAD_L / 2 + 4
    t = xcyl(11, x1, x1 + 26, LASER_Y, Z_TILT + OPT_Z)
    t = t.union(box(x1, x1 + 3, LASER_Y - 11, LASER_Y + 11, Z_TILT + OPT_Z - 23, Z_TILT + OPT_Z + 11))
    t = t.cut(xcyl(6.25 + 0.6, x1 - 1, x1 + 30, LASER_Y, Z_TILT + OPT_Z))
    t = t.cut(xcyl(M3 / 2, x1 - 1, x1 + 5, LASER_Y, Z_TILT + OPT_Z - 20))
    for a in (90, 210, 330):
        v = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        screw = (cq.Workplane('XY').cylinder(14, M3 / 2 * 0.86, direct=(0, v[0], v[1]))
                 .translate((x1 + 18, LASER_Y + v[0] * 9, Z_TILT + OPT_Z + v[1] * 9)))
        t = t.cut(screw)
    return t

# ---------- 14/15 trunnions: flange bolts to the head, shoulder presses the 6806 inner race
def trunnion(side):
    """Axis along Y through Z_TILT. Left: hollow (cables). Right: flange + 80T pulley + shoulder + tube, one print."""
    yw = HEAD_W / 2
    if side < 0:
        y_end = Y_ARM_OUT + 2.0
        t = ycyl(23, yw, yw + 4, 0, Z_TILT)                                      # flange (outside the head wall)
        t = t.union(ycyl(TB_ID / 2 + 2.0, yw + 4 - 0.01, Y_ARM_IN, 0, Z_TILT))   # shoulder -> inner race
        t = t.union(ycyl(TB_ID / 2 - RACE_FIT / 2, Y_ARM_IN - 0.01, y_end, 0, Z_TILT))
        for (x, z) in polar(3, TRUN_BOLT_R):
            t = t.cut(ycyl(M3 / 2, yw - 1, yw + 5, x, Z_TILT + z))
            t = t.cut(cq.Workplane('XZ').workplane(offset=-(yw + 4.1)).center(x, Z_TILT + z)
                      .polygon(6, M3_NUT_AF / math.cos(math.pi / 6)).extrude(2.6))
        t = t.cut(ycyl(TRUN_BORE_L, yw - 1, y_end + 1, 0, Z_TILT))
        return t.mirror('XZ')
    pul, ph = gt2_pulley(T_BIG, BELT_W)                     # along Z, 0..ph
    pul = pul.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, Y_PUL0, Z_TILT))
    t = ycyl(23, yw, Y_PUL0 + 0.01, 0, Z_TILT).union(pul)
    t = t.union(ycyl(TB_ID / 2 + 2.0, Y_PUL0 + ph - 0.01, Y_ARM_IN_R, 0, Z_TILT))
    t = t.union(ycyl(TB_ID / 2 - RACE_FIT / 2, Y_ARM_IN_R - 0.01, Y_TRUN_END, 0, Z_TILT))
    t = t.cut(ycyl(TRUN_BORE_R, yw - 1, Y_TRUN_END - 4, 0, Z_TILT))             # lightening; the end stays closed
    for (x, z) in polar(3, TRUN_BOLT_R):                                         # M3 x 12 from inside the head (self-tap)
        t = t.cut(ycyl(M3 / 2 * 0.86, yw - 1, yw + 11, x, Z_TILT + z))
    t = t.cut(ycyl(MAG_D / 2 + 0.1, Y_TRUN_END - MAG_T - 0.1, Y_TRUN_END + 1, 0, Z_TILT))   # tilt magnet
    return t

# ---------- 16/17 electronics box + lid: UNO + CNC shield V3 inside
BOX_L, BOX_W, BOX_H = 170.0, 110.0, 60.0
UNO_HOLES = ((15.2, 2.5), (66.0, 7.6), (66.0, 35.5), (13.9, 50.8))     # UNO R3 mounting holes (mm)
UNO_AT = (40.0, 8.0)                  # UNO's USB-B edge 8 mm from the front wall
def ebox():
    b = box(0, BOX_L, 0, BOX_W, 0, BOX_H).edges('|Z').fillet(6)
    b = b.cut(box(2.4, BOX_L - 2.4, 2.4, BOX_W - 2.4, 2.4, BOX_H + 1).edges('|Z').fillet(4))
    b = b.cut(xcyl(5.6, -1, 3.5, 20, 16))                              # DC jack 11.2 mm panel hole
    b = b.cut(box(-1, 3.5, 36, 56, 10, 23))                            # rocker switch 19 x 12.5
    b = b.cut(xcyl(8, -1, 3.5, 78, 20))                                # fuse holder
    b = b.cut(box(BOX_L - 3.5, BOX_L + 1, 12, 98, 12, 36))             # cable exit to the rig (grommet/clip)
    b = b.cut(box(UNO_AT[0] + 28, UNO_AT[0] + 48, -1, 3.5, 8, 26))     # UNO USB-B to laptop
    for i in range(6):
        b = b.cut(box(60 + i * 9, 64 + i * 9, BOX_W - 3.5, BOX_W + 1, 14, 38))   # vents
    for (x, y) in ((8, 8), (BOX_L - 8, 8), (8, BOX_W - 8), (BOX_L - 8, BOX_W - 8)):
        b = b.union(cyl(4.5, BOX_H - 3, 0, x, y)).cut(cyl(M3 / 2 * 0.86, BOX_H, 4, x, y))
    for (hx, hy) in UNO_HOLES:                                         # UNO standoffs (USB faces the front wall)
        x, y = UNO_AT[0] + hy, UNO_AT[1] + hx
        b = b.union(cyl(3.5, 8, 2, x, y)).cut(cyl(M3 / 2 * 0.86, 9, 3, x, y))
    for (x, y) in ((135, 30), (135, 80)):                              # MOSFET module + TCA9548A
        b = b.union(cyl(3.2, 6, 2, x, y)).cut(cyl(1.1, 7, 3, x, y))
    return b

def ebox_lid():
    l = box(0, BOX_L, 0, BOX_W, 0, 2.4).edges('|Z').fillet(6)
    l = l.union(box(2.8, BOX_L - 2.8, 2.8, BOX_W - 2.8, 2.4, 5).cut(box(5, BOX_L - 5, 5, BOX_W - 5, 2, 6)))
    for (x, y) in ((8, 8), (BOX_L - 8, 8), (8, BOX_W - 8), (BOX_L - 8, BOX_W - 8)):
        l = l.cut(cyl(M3 / 2, 10, -1, x, y))
    l = l.cut(cyl(19.5, 5, -1, 70, 55))                                   # 40 mm fan over the drivers
    for (dx, dy) in ((-16, -16), (16, -16), (-16, 16), (16, 16)):
        l = l.cut(cyl(M3 / 2 * 0.86 + 0.3, 10, -1, 70 + dx, 55 + dy))
    return l

# ---------- 00 test coupon (print first): both bearing pockets, both race pins, M3 nut + tap holes
def test_coupon():
    c = box(0, 130, 0, 62, 0, 9)
    c = c.cut(cyl((PB_OD + BRG_PRESS) / 2, 7.2, 1.9, 32, 31))
    c = c.cut(cyl((TB_OD + BRG_PRESS) / 2, 7.2, 1.9, 92, 31))
    c = c.cut(cyl(M3 / 2, 10, -1, 121, 12)).cut(hexnut_pocket_z(121, 12, -0.1, 3, M3_NUT_AF))
    c = c.cut(cyl(M3 / 2 * 0.86, 10, -1, 121, 50))
    pin_pan = ring(PB_ID / 2 - RACE_FIT / 2, SPINDLE_BORE_R, 10, 0).translate((32, 90, 0))
    pin_tilt = ring(TB_ID / 2 - RACE_FIT / 2, TRUN_BORE_L, 10, 0).translate((92, 90, 0))
    return c.union(pin_pan).union(pin_tilt)

# ============================================================== BOUGHT PARTS (for the viewer + clearance)
def nema17_along(axis_pt, direction, shaft_len=NEMA_SHAFT_LEN):
    body = box(-NEMA / 2, NEMA / 2, -NEMA / 2, NEMA / 2, -NEMA_LEN, 0).edges('|Z').chamfer(4)
    boss = cyl(NEMA_PILOT / 2, 2, 0)
    shaft = cyl(NEMA_SHAFT / 2, shaft_len, 0)
    return orient(body, direction, axis_pt), orient(boss.union(shaft), direction, axis_pt)

def orient(shape, direction, pt):
    d = direction
    if d == '+z': s = shape
    elif d == '-z': s = shape.rotate((0, 0, 0), (1, 0, 0), 180)
    elif d == '-y': s = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    elif d == '+y': s = shape.rotate((0, 0, 0), (1, 0, 0), -90)
    else: raise ValueError(d)
    return s.translate(pt)

def pulley20(z_center_belt=0.0, hub_down=False):
    """GT2 20T metal pulley: teeth +/-3.5 about the belt plane, flanges to +/-4.5, 7 mm hub on one side."""
    p = cyl(8, 1, -4.5).union(cyl(PD_SMALL / 2 - 0.25, 7, -3.5)).union(cyl(8, 1, 3.5))
    p = p.union(cyl(6.5, 7, -11.5) if hub_down else cyl(6.5, 7, 4.5))
    return p.cut(cyl(NEMA_SHAFT / 2, 30, -15)).translate((0, 0, z_center_belt))

def bearing(od, bore, w):
    return cyl(od / 2, w, 0).cut(cyl(bore / 2, w + 2, -1))

def belt_loop(c1, r1, c2, r2, width, thickness=1.4, n=90):
    """closed belt around two pulleys in the XY plane (pitch radii r1, r2), extruded to 'width'."""
    import numpy as np
    (x1, y1), (x2, y2) = c1, c2
    d = math.hypot(x2 - x1, y2 - y1)
    ang = math.atan2(y2 - y1, x2 - x1)
    phi = math.asin((r1 - r2) / d)
    t = math.pi / 2 + phi
    pts = [(x1 + r1 * math.cos(a), y1 + r1 * math.sin(a)) for a in np.linspace(ang + t, ang + 2 * math.pi - t, n)] + \
          [(x2 + r2 * math.cos(a), y2 + r2 * math.sin(a)) for a in np.linspace(ang - t, ang + t, n)]
    outer = cq.Workplane('XY').polyline([(x1 + (r1 + thickness) * math.cos(a), y1 + (r1 + thickness) * math.sin(a)) for a in np.linspace(ang + t, ang + 2 * math.pi - t, n)]
                                        + [(x2 + (r2 + thickness) * math.cos(a), y2 + (r2 + thickness) * math.sin(a)) for a in np.linspace(ang - t, ang + t, n)]).close().extrude(width)
    inner = cq.Workplane('XY').polyline(pts).close().extrude(width + 2).translate((0, 0, -1))
    return outer.cut(inner)

def camera_board():
    b = box(0, 1.6, -19, 19, -19, 19)
    lens = xcyl(7, 1.6, 12, 0, 0).union(xcyl(8.5, 12, 22, 0, 0))
    return b.union(lens)

def laser_module():
    return xcyl(6, 0, 30, 0, 0).union(xcyl(6.4, 26, 30, 0, 0))

def as5600_board():
    """board z 0..1.6, chip on top 1.6..2.6"""
    return box(-11.5, 11.5, -11.5, 11.5, 0, 1.6).union(box(-2, 2, -2, 2, 1.6, 2.6))

# ============================================================== build everything
def build():
    tt, z_pul0, ph = pan_turntable()
    mx = X_PAN_MOTOR
    # --- printed
    add('01_base_hub', base_hub(), 'fixed', '#9aa0a8', note='Base hub: two 6808 bearings, open centre for cables, pan motor tower')
    for i, a in enumerate(LEG_DEG):
        add(f'02_leg_{i + 1}', leg(a), 'fixed', '#8b9098', note='Tripod leg (print 3)')
    add('03_pan_sensor_bridge', pan_sensor_bridge(), 'fixed', '#6f7680', note='Holds the pan AS5600 over the pan motor shaft')
    add('04_magnet_cap', magnet_cap().translate((mx, 0, PAN_CAP_Z0)), 'fixed', '#e0e0e0', note='Magnet cap on the pan motor shaft')
    add('05_spindle_washer', spindle_washer(), 'pan', '#e0e0e0', note='Clamps the lower pan bearing (3 x M3)')
    add('06_pan_turntable', tt, 'pan', '#a7adb5', note='Hollow spindle + 80T pulley + deck, one print')
    add('07_arm_right', arm(+1), 'pan', '#9aa0a8', note='Yoke arm, belt side (6806 bearing, motor-plate standoffs)')
    add('08_arm_left', arm(-1), 'pan', '#9aa0a8', note='Yoke arm, cable side (6806 bearing)')
    add('09_tilt_motor_plate', tilt_motor_plate(), 'pan', '#7d848e', note='Tilt motor plate: stands on the deck under the head')
    add('10_tilt_sensor_bracket', tilt_sensor_bracket(), 'pan', '#6f7680', note='Tilt sensor bracket, outside the right arm')
    add('11_head', head(), 'tilt', '#2b2e33', note='Optics head (camera + laser bench)')
    add('12_front_plate', front_plate(), 'tilt', '#1f2226', note='Camera board plate')
    add('13_laser_holder', laser_holder(), 'tilt', '#1f2226', note='Laser tube with 3 alignment screws')
    add('14_trunnion_left', trunnion(-1), 'tilt', '#c3c7cd', note='Left trunnion: hollow, cables pass through')
    add('15_trunnion_right', trunnion(+1), 'tilt', '#c3c7cd', note='Right trunnion with the 80T tilt pulley built in')
    add('16_electronics_box', ebox().translate((-330, -55, 0)), 'desk', '#3a3f46', note='Electronics box (UNO + CNC shield)')
    add('17_electronics_lid', ebox_lid().rotate((0, 0, 0), (1, 0, 0), 180).translate((-330, 55, BOX_H + 2.4)), 'desk', '#4a5058', note='Box lid with fan opening')
    add('00_test_coupon', test_coupon().translate((-330, 140, 0)), 'desk', '#e7c96a', note='Fit test (print FIRST)')

    # --- bought
    pan_body, pan_shaft = nema17_along((mx, 0, Z_PAN_PLATE), '+z')
    add('m_pan_motor', pan_body, 'fixed', '#1c1d20', printed=False, note='NEMA17 (reuse MK2)')
    add('m_pan_motor_shaft', pan_shaft, 'fixed', '#c9ccd1', printed=False)
    add('m_pan_pulley20', pulley20(PAN_PUL20_Z, hub_down=True).translate((mx, 0, 0)), 'fixed', '#c9ccd1', printed=False, note='GT2 20T 5 mm bore (hub down)')
    add('m_pan_belt', belt_loop((0, 0), PD_BIG / 2, (mx, 0), PD_SMALL / 2, BELT_W).translate((0, 0, Z_BELT_PAN - BELT_W / 2)), 'fixedbelt', '#111214', printed=False, note=f'GT2 6 mm closed belt {BELT_PAN_L:.0f} mm (240 also fits)')
    add('m_brg_pan_low', bearing(*PAN_BRG).translate((0, 0, Z_BRG_LOW)), 'fixed', '#d7dade', printed=False, note='6808-2RS')
    add('m_brg_pan_top', bearing(*PAN_BRG).translate((0, 0, Z_HUB_TOP - PB_W)), 'fixed', '#d7dade', printed=False, note='6808-2RS')
    add('m_pan_as5600', as5600_board().rotate((0, 0, 0), (1, 0, 0), 180).translate((mx, 0, PAN_BOARD_Z + 1.6)), 'fixed', '#1d6fd1', printed=False, note='AS5600 (pan, reads the motor)')
    zm, xm = Z_TILT_MOTOR, TILT_MOTOR_X
    tilt_body = box(xm - NEMA / 2, xm + NEMA / 2, Y_TPLATE - NEMA_LEN, Y_TPLATE, zm - NEMA / 2, zm + NEMA / 2).edges('|Y').chamfer(4)
    add('m_tilt_motor', tilt_body, 'pan', '#1c1d20', printed=False, note='NEMA17 (reuse MK2), on the deck under the head')
    add('m_tilt_motor_shaft', ycyl(NEMA_SHAFT / 2, Y_TPLATE, Y_TPLATE + NEMA_SHAFT_LEN, xm, zm), 'pan', '#c9ccd1', printed=False)
    add('m_tilt_pulley20', pulley20(0, hub_down=True).rotate((0, 0, 0), (1, 0, 0), -90).translate((xm, Y_BELT_TILT, zm)), 'pan', '#c9ccd1', printed=False, note='GT2 20T 5 mm bore')
    tbelt = belt_loop((0, 0), PD_BIG / 2, (xm, zm - Z_TILT), PD_SMALL / 2, BELT_W)
    tbelt = tbelt.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, Y_BELT_TILT + BELT_W / 2, Z_TILT))
    add('m_tilt_belt', tbelt, 'pan', '#111214', printed=False, note=f'GT2 6 mm closed belt {BELT_TILT_L:.0f} mm')
    add('m_brg_tilt_r', bearing(*TILT_BRG).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, Y_ARM_IN_R, Z_TILT)), 'pan', '#d7dade', printed=False, note='6806-2RS')
    add('m_brg_tilt_l', bearing(*TILT_BRG).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -Y_ARM_IN - TB_W, Z_TILT)), 'pan', '#d7dade', printed=False, note='6806-2RS')
    add('m_tilt_as5600', as5600_board().rotate((0, 0, 0), (1, 0, 0), 90).translate((0, Y_TSENSOR - 0.1, Z_TILT)), 'pan', '#1d6fd1', printed=False, note='AS5600 (tilt)')
    add('m_camera', camera_board().translate((HEAD_L / 2 + 4, CAM_Y, Z_TILT + OPT_Z)), 'tilt', '#1f7a4a', printed=False, note='USB camera board 38x38')
    add('m_laser', laser_module().translate((HEAD_L / 2 + 2, LASER_Y, Z_TILT + OPT_Z)), 'tilt', '#b08a2e', printed=False, note='12 mm laser module')

build()

# ============================================================== export
import trimesh

def to_mesh(shape, tol=0.08):
    v, f = shape.val().tessellate(tol, 0.3)
    return trimesh.Trimesh([(p.x, p.y, p.z) for p in v], f, process=True)

report = {'belts': {}, 'parts': {}, 'clearance': {}, 'params': {}}
report['belts'] = {
    'ratio': T_BIG / T_SMALL,
    'pan': {'belt_mm': BELT_PAN_L, 'teeth': BELT_PAN_L / 2, 'centre_mm': round(C_PAN, 2), 'motor_x_mm': round(X_PAN_MOTOR, 2),
            'belts_that_fit_mm': [L for L in range(220, 260) if -PAN_SLIDE_IN <= belt_center_distance(L, T_SMALL, T_BIG) - C_PAN <= PAN_SLIDE_OUT]},
    'tilt': {'belt_mm': BELT_TILT_L, 'teeth': BELT_TILT_L / 2, 'centre_mm': round(C_TILT, 2), 'motor_z_mm': round(Z_TILT_MOTOR, 2),
             'belts_that_fit_mm': [L for L in range(260, 300) if abs(belt_center_distance(L, T_SMALL, T_BIG) - C_TILT) <= TILT_SLIDE * (Z_TILT - Z_TILT_MOTOR) / C_TILT]},
    'steps_per_output_deg': 200 * 16 * (T_BIG / T_SMALL) / 360.0,
}
report['params'] = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float))}

meshes = {}
for name, P in PARTS.items():
    m = to_mesh(P['shape'])
    meshes[name] = m
    m.export(os.path.join(VIEW_DIR, name + '.stl'))
    info = {'group': P['group'], 'printed': P['printed'], 'colour': P['colour'], 'note': P['note'],
            'volume_cm3': round(abs(m.volume) / 1000, 2), 'bbox_mm': [round(x, 1) for x in (m.bounds[1] - m.bounds[0])],
            'watertight': bool(m.is_watertight)}
    if P['printed']:
        # print file: lay the part on Z=0 in a sensible orientation
        pm = m.copy()
        # arms: right arm inner face down (standoffs point up, pocket ceiling is a 3 mm ring);
        # left arm outer face down (pocket opens up). Trunnions and pulley: flange on the bed.
        orient_rules = {'06_pan_turntable': ('flip',), '07_arm_right': ('rotx', 90), '08_arm_left': ('rotx', 90),
                        '09_tilt_motor_plate': ('rotx', 90), '11_head': (),
                        '12_front_plate': ('roty', 90), '13_laser_holder': ('roty', 90),
                        '14_trunnion_left': ('rotx', -90), '15_trunnion_right': ('rotx', 90), '10_tilt_sensor_bracket': ('rotx', -90),
                        '03_pan_sensor_bridge': ('flip',), '17_electronics_lid': ('flip',)}
        r = orient_rules.get(name, ())
        if name.startswith('02_leg'):
            ang = -LEG_DEG[int(name[-1]) - 1]
            pm.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), (0, 0, 1)))
        if r and r[0] == 'flip':
            pm.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (1, 0, 0)))
        elif r and r[0] == 'rotx':
            pm.apply_transform(trimesh.transformations.rotation_matrix(math.radians(r[1]), (1, 0, 0)))
        elif r and r[0] == 'roty':
            pm.apply_transform(trimesh.transformations.rotation_matrix(math.radians(r[1]), (0, 1, 0)))
        pm.apply_translation(-pm.bounds[0] + [0, 0, 0])
        pm.apply_translation([-(pm.bounds[1][0]) / 2, -(pm.bounds[1][1]) / 2, 0])
        pm.export(os.path.join(PRINT_DIR, name + '.stl'))
        try:
            cq.exporters.export(P['shape'], os.path.join(STEP_DIR, name + '.step'))
        except Exception as e:
            info['step_error'] = str(e)
        info['print_bbox_mm'] = [round(x, 1) for x in (pm.bounds[1] - pm.bounds[0])]
        # rough grams: shells (4 walls, 5 top/bottom) + 40% gyroid; PETG 1.27 g/cm3
        area = pm.area / 100.0            # cm2
        shell = min(abs(m.volume) / 1000, area * 0.16)
        inner = max(0.0, abs(m.volume) / 1000 - shell)
        info['grams_petg'] = round((shell + inner * 0.40) * 1.27, 1)
    report['parts'][name] = info

# ---------- clearance: intersect moving groups over the pan/tilt range
import numpy as np
def T_pan(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (0, 0, 1))
def T_tilt(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (0, 1, 0), (0, 0, Z_TILT))

groups = {}
for name, P in PARTS.items():
    groups.setdefault(P['group'], []).append(name)
def merged(names):
    return trimesh.util.concatenate([meshes[n] for n in names])

# designed contacts that are not collisions
IGNORE = {('m_pan_motor_shaft', 'm_pan_pulley20'), ('m_pan_motor_shaft', '04_magnet_cap'), ('m_pan_motor_shaft', 'm_pan_motor'),
          ('m_tilt_motor_shaft', 'm_tilt_pulley20'), ('m_tilt_motor_shaft', 'm_tilt_motor'),
          ('m_pan_belt', '06_pan_turntable'), ('m_pan_belt', 'm_pan_pulley20'),
          ('m_tilt_belt', '15_trunnion_right'), ('m_tilt_belt', 'm_tilt_pulley20'),
          # running fits: 0.025 mm radial gap by design, smaller than the mesh facets, so rotated copies graze
          ('m_brg_pan_low', '06_pan_turntable'), ('m_brg_pan_top', '06_pan_turntable'),
          ('m_brg_tilt_r', '15_trunnion_right'), ('m_brg_tilt_l', '14_trunnion_left')}

def overlap(a, b):
    try:
        i = a.intersection(b, engine='manifold')
        return float(abs(i.volume)) if not i.is_empty else 0.0
    except Exception:
        return -1.0

def check(names_a, names_b, Ta, Tb, label):
    worst = []
    for na in names_a:
        ma = meshes[na].copy(); ma.apply_transform(Ta)
        for nb in names_b:
            if (na, nb) in IGNORE or (nb, na) in IGNORE:
                continue
            mb = meshes[nb].copy(); mb.apply_transform(Tb)
            if not ma.bounds_intersect if False else False:
                pass
            if (ma.bounds[0] > mb.bounds[1]).any() or (mb.bounds[0] > ma.bounds[1]).any():
                continue
            v = overlap(ma, mb)
            if v > 1.0 or v < 0:
                worst.append((na, nb, round(v, 1)))
    return worst

fixed = groups['fixed'] + groups.get('fixedbelt', [])
pan = groups['pan']
tilt = groups['tilt']
res = {}
# standing still: no two parts may share material (catches bolted parts that were drawn into each other)
allp = fixed + pan + tilt
bad_static = []
for i, na in enumerate(allp):
    bad_static += check([na], allp[i + 1:], np.eye(4), np.eye(4), '')
res['static @pan0 tilt0'] = bad_static
for p in (0, 60, 120, 150, -60, -120, -150):
    res[f'fixed-vs-pan @pan{p}'] = check(fixed, pan + tilt, np.eye(4), T_pan(p), '')
for tdeg in (-45, -30, 0, 30, 45, 60):
    res[f'pan-vs-tilt @tilt{tdeg}'] = check(pan, tilt, np.eye(4), T_tilt(tdeg), '')
    res[f'fixed-vs-tilt @tilt{tdeg}'] = check(fixed, tilt, np.eye(4), T_tilt(tdeg), '')
report['clearance'] = {k: v for k, v in res.items()}
report['clearance_ok'] = all(len(v) == 0 for v in res.values())
report['assembly_bbox_mm'] = [round(x, 1) for x in (merged(fixed + pan + tilt).bounds[1] - merged(fixed + pan + tilt).bounds[0])]

with open(os.path.join(OUT, 'report.json'), 'w') as f:
    json.dump(report, f, indent=1)
# viewer manifest
manifest = [{'name': n, 'group': P['group'], 'colour': P['colour'], 'printed': P['printed'], 'note': P['note']} for n, P in PARTS.items()]
with open(os.path.join(VIEW_DIR, 'manifest.json'), 'w') as f:
    json.dump({'parts': manifest, 'z_tilt': Z_TILT, 'belts': report['belts']}, f, indent=1)
print(json.dumps({'belts': report['belts'], 'clearance_ok': report['clearance_ok'],
                  'bad': {k: v for k, v in res.items() if v}}, indent=1))
