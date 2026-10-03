"""Plan Urena · MK3 TOWER edition: direct-drive pan-tilt on a 3-leg tripod (CadQuery).

Two NEMA17 steppers, no belts, no bearings to buy. Run:

    python3 tools/mk3/tower_cad.py

Outputs
    tools/mk3/tower/out/print/*.stl    parts to print, each lying in its print orientation
    tools/mk3/tower/out/step/*.step    the same parts as STEP
    tools/mk3/tower/out/assembly/*.stl every part (bought + printed) in place, for renders
    tools/mk3/tower/out/report.json    sizes, grams, clearance over the full pan / tilt sweep

Units mm. Z up. The pan axis is Z. At pan 0 the camera looks along +X. The tilt axis is
parallel to Y (the tilt motor lies on its side). Ground is Z = 0.

Layout (bottom to top):  tripod base -> tower sleeve (pan motor hangs inside from the cap)
-> cap -> pan hub (clamped on the pan shaft) -> tilt mount (plate + wall) carrying the tilt
motor on its side -> head clamped on the tilt shaft (camera + laser), beside the motor.
"""
import json, math, os
import cadquery as cq
import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'tower', 'out')
PRINT_DIR, STEP_DIR, ASM_DIR = (os.path.join(OUT, d) for d in ('print', 'step', 'assembly'))
for d in (PRINT_DIR, STEP_DIR, ASM_DIR):
    os.makedirs(d, exist_ok=True)

# ============================================================== PARAMETERS
HOLE_CLEAR = 0.25                       # printed holes come out small
NEMA, NEMA_HOLES, NEMA_PILOT, NEMA_LEN = 42.3, 31.0, 22.0, 40.0   # NEMA17, 40 mm body
NEMA_SHAFT, NEMA_SHAFT_LEN = 5.0, 24.0
M3 = 3.2                                # M3 clearance hole
M3_TAP = 2.7                            # pilot hole for an M3 screw cutting its own thread in PETG
M3_HEAD, M3_NUT_AF, M3_NUT_T = 6.2, 5.9, 2.6
BORE = NEMA_SHAFT + 0.2                 # shaft bore in the hub and the head

# tripod base
BASE_T = 6.0
PAD = 80.0                              # square pad the sleeve sits on
ARM_LEN, ARM_W0, ARM_W1 = 108.0, 36.0, 18.0
ARM_ANGLES = (90.0, 210.0, 330.0)       # one leg under the head side (+Y)
FL = 74.0                               # sleeve foot flange, square
FL_T = 4.0
FL_HOLE = 33.0                          # flange bolt holes at (+/-33, +/-33)

# tower
SL_OUT, SL_IN = 60.0, NEMA + 2.3        # sleeve outside / motor cavity (44.6)
Z_SL0 = BASE_T
Z_SL1 = 52.0                            # top of the sleeve = underside of the cap = pan motor flange face
CAP_T = 4.0
Z_CAP1 = Z_SL1 + CAP_T                  # 56
CORNER = 26.3                           # cap screws into the sleeve corners at (+/-26.3, +/-26.3)

# pan hub and tilt mount
HUB_H, HUB_R, HUB_FL_R = 16.0, 13.0, 17.0
Z_HUB0 = Z_CAP1 + 1.0                   # 1 mm above the cap so it never rubs
Z_HUB1 = Z_HUB0 + HUB_H                 # 73
HUB_SCREW_R = 11.5                      # three M3 screws down into the hub
PLATE_T = 6.0
Z_PL0, Z_PL1 = Z_HUB1, Z_HUB1 + PLATE_T # 73..79
PLATE_X, PLATE_Y0, PLATE_Y1 = 26.0, -24.0, 23.2
WALL_T = 3.2
Y_FLANGE = 20.0                         # tilt motor flange face (motor body is y -20..+20)
Z_TILT = Z_PL1 + NEMA / 2               # tilt axis height
WALL_Y0, WALL_Y1 = Y_FLANGE, Y_FLANGE + WALL_T
WALL_TOP = Z_TILT + 24.0

# head
HB_Y0, HB_Y1 = WALL_Y1 + 1.8, WALL_Y1 + 1.8 + 18.0      # clamp boss on the tilt shaft
HB_R = 10.0
ARM_X1 = 30.0
CAM = 38.6                               # 38 x 38 mm USB camera board pocket
CAM_Y0 = HB_Y0 + 0.5
CAM_Y1 = CAM_Y0 + CAM + 1.0 + 0.2
CAM_YC = (CAM_Y0 + CAM_Y1) / 2
PLATE_X0, PLATE_X1 = ARM_X1, ARM_X1 + 4.0
LASER_D, LASER_Z = 12.3, 27.0            # 12 mm laser module, boss centre above the tilt axis

# ============================================================== helpers
def cyl(r, h, z0=0.0, x=0.0, y=0.0):
    return cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(r).extrude(h)

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def ycyl(r, y0, y1, x=0.0, z=0.0):
    return cq.Workplane('XZ').workplane(offset=-y1).center(x, z).circle(r).extrude(y1 - y0)

def xcyl(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane('YZ').workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)

def rot_z(shape, deg):
    return shape.rotate((0, 0, 0), (0, 0, 1), deg)

PARTS = {}
def add(name, shape, group, colour, printed=True, qty=1, note=''):
    PARTS[name] = dict(shape=shape, group=group, colour=colour, printed=printed, qty=qty, note=note)

# ============================================================== PRINTED PARTS
def tripod_base():
    pad = box(-PAD / 2, PAD / 2, -PAD / 2, PAD / 2, 0, BASE_T).edges('|Z').fillet(6)
    solid = pad
    for a in ARM_ANGLES:
        pts = [(0, -ARM_W0 / 2), (ARM_LEN, -ARM_W1 / 2), (ARM_LEN, ARM_W1 / 2), (0, ARM_W0 / 2)]
        arm = cq.Workplane('XY').polyline(pts).close().extrude(BASE_T).edges('|Z and >X').fillet(ARM_W1 / 2 - 0.5)
        hole = (cq.Workplane('XY').polyline([(PAD / 2 + 4, -ARM_W0 / 2 + 7.5), (ARM_LEN - 18, -ARM_W1 / 2 + 5.2),
                                              (ARM_LEN - 18, ARM_W1 / 2 - 5.2), (PAD / 2 + 4, ARM_W0 / 2 - 7.5)]).close().extrude(BASE_T + 2).translate((0, 0, -1)))
        arm = arm.cut(hole)
        solid = solid.union(rot_z(arm, a))
    for sx in (-1, 1):
        for sy in (-1, 1):
            solid = solid.cut(cyl(M3 / 2, BASE_T + 2, -1, sx * FL_HOLE, sy * FL_HOLE))
            # nut pocket on the underside
            solid = solid.cut(cq.Workplane('XY').workplane(offset=-0.1).center(sx * FL_HOLE, sy * FL_HOLE)
                              .polygon(6, M3_NUT_AF / math.cos(math.pi / 6)).extrude(M3_NUT_T + 0.3))
    solid = solid.cut(cyl(12, BASE_T + 2, -1))       # cable / finger hole in the middle
    return solid

def tower_sleeve():
    s = box(-SL_OUT / 2, SL_OUT / 2, -SL_OUT / 2, SL_OUT / 2, Z_SL0, Z_SL1).edges('|Z').fillet(3)
    s = s.union(box(-FL / 2, FL / 2, -FL / 2, FL / 2, Z_SL0, Z_SL0 + FL_T).edges('|Z').fillet(5))
    s = s.cut(box(-SL_IN / 2, SL_IN / 2, -SL_IN / 2, SL_IN / 2, Z_SL0 - 1, Z_SL1 + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = s.cut(cyl(M3 / 2, FL_T + 2, Z_SL0 - 1, sx * FL_HOLE, sy * FL_HOLE))            # flange bolts
            s = s.cut(cyl(M3_TAP / 2, 12, Z_SL1 - 12, sx * CORNER, sy * CORNER))                # cap screws (self-tapping M3)
    s = s.cut(box(-7, 7, -SL_OUT / 2 - 1, -SL_IN / 2 + 1, Z_SL0 + FL_T + 1, Z_SL0 + FL_T + 13))  # motor cable slot, -Y wall
    return s

def tower_cap():
    c = box(-SL_OUT / 2, SL_OUT / 2, -SL_OUT / 2, SL_OUT / 2, Z_SL1, Z_CAP1).edges('|Z').fillet(3)
    c = c.cut(cyl((NEMA_PILOT + 0.3) / 2, CAP_T + 2, Z_SL1 - 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = c.cut(cyl(M3 / 2, CAP_T + 2, Z_SL1 - 1, sx * NEMA_HOLES / 2, sy * NEMA_HOLES / 2))     # pan motor screws
            c = c.cut(cyl(M3 / 2, CAP_T + 2, Z_SL1 - 1, sx * CORNER, sy * CORNER))                     # cap to sleeve
    return c

def pan_hub():
    prof = [(0, 0), (HUB_R, 0), (HUB_R, 9), (HUB_FL_R, 13), (HUB_FL_R, HUB_H), (0, HUB_H)]
    h = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((0, 0, Z_HUB0))
    h = h.cut(cyl(BORE / 2, HUB_H + 2, Z_HUB0 - 1))
    zs = Z_HUB0 + 8.0
    h = h.cut(xcyl(M3 / 2, 0, HUB_R + 2, 0, zs))                                     # set screw onto the shaft flat
    h = h.cut(box(5.6, 5.6 + M3_NUT_T + 0.2, -M3_NUT_AF / 2, M3_NUT_AF / 2, zs - M3_NUT_AF / 2, Z_HUB1 + 1))   # nut slot, open at the top
    for a in (90, 210, 330):
        x, y = HUB_SCREW_R * math.cos(math.radians(a)), HUB_SCREW_R * math.sin(math.radians(a))
        h = h.cut(cyl(M3_TAP / 2, 9, Z_HUB1 - 9, x, y))
    return h

def tilt_mount():
    p = box(-PLATE_X, PLATE_X, PLATE_Y0, PLATE_Y1, Z_PL0, Z_PL1).edges('|Z').fillet(4)
    w = box(-PLATE_X, PLATE_X, WALL_Y0, WALL_Y1, Z_PL0, WALL_TOP).edges('|Y and >Z').fillet(6)
    m = p.union(w)
    for x0 in (22.0, -26.0):                                                        # side gussets, plate to wall
        g = (cq.Workplane('YZ').workplane(offset=x0)
             .polyline([(WALL_Y0 + 0.5, Z_PL1 - 0.5), (WALL_Y0 + 0.5, Z_TILT + 14), (-2, Z_PL1 - 0.5)]).close().extrude(4.0))
        m = m.union(g)
    # tilt motor: pilot + 4 screws through the wall (shaft axis along Y)
    m = m.cut(ycyl((NEMA_PILOT + 0.3) / 2, WALL_Y0 - 1, WALL_Y1 + 1, 0, Z_TILT))
    for sx in (-1, 1):
        for sz in (-1, 1):
            m = m.cut(ycyl(M3 / 2, WALL_Y0 - 1, WALL_Y1 + 1, sx * NEMA_HOLES / 2, Z_TILT + sz * NEMA_HOLES / 2))
    # pan: shaft-tip pocket from below, three screw counterbores + holes
    m = m.cut(cyl(3.0, 3.5, Z_PL0 - 0.01))
    for a in (90, 210, 330):
        x, y = HUB_SCREW_R * math.cos(math.radians(a)), HUB_SCREW_R * math.sin(math.radians(a))
        m = m.cut(cyl(M3 / 2 + 0.1, PLATE_T + 2, Z_PL0 - 1, x, y))
        m = m.cut(cyl(M3_HEAD / 2 + 0.2, 3.2, Z_PL1 - 3.0, x, y))
    return m

def head():
    zc = Z_TILT
    boss = ycyl(HB_R, HB_Y0, HB_Y1, 0, zc)
    arm = box(8, ARM_X1 + 0.5, HB_Y0, CAM_Y1, zc - 10, zc + 10)
    plate = box(PLATE_X0, PLATE_X1, HB_Y0, CAM_Y1, zc - 22, zc + LASER_Z + 9.5).edges('|X').fillet(3)
    web = box(0, ARM_X1, HB_Y0, HB_Y1, zc - 10, zc + 10)
    laser = xcyl(9.0, ARM_X1, ARM_X1 + 30, CAM_YC, zc + LASER_Z)
    h = boss.union(arm).union(web).union(plate).union(laser)
    h = h.cut(ycyl(BORE / 2, HB_Y0 - 1, HB_Y1 + 1, 0, zc))                          # tilt shaft bore
    xs = -1.0
    h = h.cut(xcyl(M3 / 2, -HB_R - 1, 0, (HB_Y0 + HB_Y1) / 2, zc))                  # shaft set screw (from the rear)
    h = h.cut(box(-8.6, -8.6 + M3_NUT_T + 0.2, (HB_Y0 + HB_Y1) / 2 - M3_NUT_AF / 2, (HB_Y0 + HB_Y1) / 2 + M3_NUT_AF / 2, zc - M3_NUT_AF / 2, zc + HB_R + 1))
    # camera: pocket in the front face + lens window
    h = h.cut(box(PLATE_X1 - 2.4, PLATE_X1 + 1, CAM_YC - CAM / 2, CAM_YC + CAM / 2, zc - CAM / 2, zc + CAM / 2))
    h = h.cut(xcyl(9.5, PLATE_X0 - 1, PLATE_X1 + 1, CAM_YC, zc))
    # laser bore + light clamp screw from the top
    h = h.cut(xcyl(LASER_D / 2, ARM_X1 - 1, ARM_X1 + 31, CAM_YC, zc + LASER_Z))
    h = h.cut(cyl(M3_TAP / 2, 14, zc + LASER_Z, ARM_X1 + 15, CAM_YC))
    return h

def test_coupon():
    """Print this first (10 min): checks the shaft bore, M3 self-tap pilot, nut slot, pilot hole and camera pocket."""
    c = box(0, 100, 0, 46, 0, 8)
    c = c.cut(cyl(BORE / 2, 10, -1, 14, 14))                               # shaft bore: a NEMA17 shaft must slide in
    c = c.cut(cyl(M3_TAP / 2, 10, 1, 34, 14))                              # M3 screw must bite, not spin
    c = c.cut(box(44, 44 + M3_NUT_T + 0.2, 14 - M3_NUT_AF / 2, 14 + M3_NUT_AF / 2, 1.5, 9))   # a hex nut must drop in
    c = c.cut(cyl((NEMA_PILOT + 0.3) / 2, 10, -1, 70, 14))                 # NEMA17 pilot boss (22 mm) must sit in
    c = c.cut(box(8, 8 + CAM, 30, 30 + 12, 4, 9))                          # camera pocket width (board 38 mm)
    c = c.cut(cyl(LASER_D / 2, 10, -1, 70, 34))                            # 12 mm laser must push in
    return c

# ============================================================== BOUGHT PARTS (for the picture and clearance)
def nema_z(z_flange, shaft_len=NEMA_SHAFT_LEN):
    """pan motor: flange face at z_flange, body hangs below, shaft up. Returns body, shaft+boss."""
    body = box(-NEMA / 2, NEMA / 2, -NEMA / 2, NEMA / 2, z_flange - NEMA_LEN, z_flange).edges('|Z').chamfer(4)
    boss = cyl(NEMA_PILOT / 2, 2, z_flange).union(cyl(NEMA_SHAFT / 2, shaft_len, z_flange))
    return body, boss

def nema_y(z_axis, y_flange):
    """tilt motor on its side: flange face at y_flange, body toward -Y, shaft toward +Y."""
    body = box(-NEMA / 2, NEMA / 2, y_flange - NEMA_LEN, y_flange, z_axis - NEMA / 2, z_axis + NEMA / 2).edges('|Y').chamfer(4)
    boss = ycyl(NEMA_PILOT / 2, y_flange, y_flange + 2, 0, z_axis)
    shaft = ycyl(NEMA_SHAFT / 2, y_flange, y_flange + NEMA_SHAFT_LEN, 0, z_axis)
    return body, boss, shaft

def build():
    add('01_tripod_base', tripod_base(), 'fixed', '#9aa3ad', note='Three legs + square pad. Flat print.')
    add('02_tower_sleeve', tower_sleeve(), 'fixed', '#b8bfc7', note='Square tower that holds the pan motor. Foot flange bolts to the base.')
    add('03_tower_cap', tower_cap(), 'fixed', '#c6ccd2', note='Top plate. The pan motor screws to its underside.')
    body, bs = nema_z(Z_SL1)
    add('m_pan_motor', body, 'fixed', '#2b2f36', printed=False, note='NEMA17 (pan), hangs inside the tower')
    add('m_pan_shaft', bs, 'pan', '#d4d8dd', printed=False, note='pan motor shaft')
    add('04_pan_hub', pan_hub(), 'pan', '#6d9bd1', note='Clamps on the pan shaft. Set screw onto the shaft flat.')
    add('05_tilt_mount', tilt_mount(), 'pan', '#5b8ac4', note='Plate + wall. The tilt motor is screwed to the wall, on its side.')
    tb, tboss, tshaft = nema_y(Z_TILT, Y_FLANGE)
    add('m_tilt_motor', tb, 'pan', '#2b2f36', printed=False, note='NEMA17 (tilt), lying on the plate')
    add('m_tilt_boss', tboss, 'pan', '#d4d8dd', printed=False, note='pilot boss')
    add('m_tilt_shaft', tshaft, 'tilt', '#d4d8dd', printed=False, note='tilt motor shaft')
    add('06_head', head(), 'tilt', '#3fae7a', note='Clamps on the tilt shaft. Holds the camera and the laser.')
    zc = Z_TILT
    add('m_camera', box(PLATE_X1 - 2.4, PLATE_X1 - 0.8, CAM_YC - 19, CAM_YC + 19, zc - 19, zc + 19).union(
        xcyl(7.5, PLATE_X1 - 0.8, PLATE_X1 + 11, CAM_YC, zc)), 'tilt', '#1c1f26', printed=False, note='USB camera board 38 x 38 mm')
    add('m_laser', xcyl(LASER_D / 2 - 0.15, ARM_X1 - 4, ARM_X1 + 34, CAM_YC, zc + LASER_Z), 'tilt', '#8a2be2', printed=False, note='12 mm laser module')
    add('00_test_coupon', test_coupon(), 'none', '#888888', note='Print first. Checks every fit in 10 minutes.')
build()

# ============================================================== meshes, print files, weights
def to_mesh(shape, tol=0.08):
    v, f = shape.val().tessellate(tol, 0.3)
    return trimesh.Trimesh([(p.x, p.y, p.z) for p in v], f, process=True)

PRINT_ROT = {'03_tower_cap': None}      # flat as modelled
report = {'parts': {}, 'clearance': {}, 'params': {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float))}}
meshes = {}
for name, P in PARTS.items():
    m = to_mesh(P['shape'])
    meshes[name] = m
    if P['group'] != 'none':
        m.export(os.path.join(ASM_DIR, name + '.stl'))
    info = {'group': P['group'], 'printed': P['printed'], 'note': P['note'], 'volume_cm3': round(abs(m.volume) / 1000, 2),
            'bbox_mm': [round(x, 1) for x in (m.bounds[1] - m.bounds[0])], 'watertight': bool(m.is_watertight)}
    if P['printed']:
        pm = m.copy()
        if name == '01_tripod_base' or name == '02_tower_sleeve' or name == '03_tower_cap' or name == '04_pan_hub' or name == '05_tilt_mount' or name == '00_test_coupon':
            pass                        # already stands on its best face as modelled (sleeve: flange down, plate: bed side down, hub: big end up)
        if name == '06_head':           # lie the camera plate flat: front face (+X) up would need supports; print with the boss end down instead
            pm.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (0, 1, 0)))
            pm.apply_transform(trimesh.transformations.rotation_matrix(math.pi, (0, 0, 1)))
        pm.apply_translation(-pm.bounds[0])
        pm.export(os.path.join(PRINT_DIR, name + '.stl'))
        try:
            cq.exporters.export(P['shape'], os.path.join(STEP_DIR, name + '.step'))
        except Exception as e:
            info['step_error'] = str(e)
        info['print_bbox_mm'] = [round(x, 1) for x in (pm.bounds[1] - pm.bounds[0])]
        area = pm.area / 100.0
        shell = min(abs(m.volume) / 1000, area * 0.16)
        inner = max(0.0, abs(m.volume) / 1000 - shell)
        info['grams_petg'] = round((shell + inner * 0.25) * 1.27, 1)
    report['parts'][name] = info

# ============================================================== clearance over the whole sweep
def T_pan(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (0, 0, 1))
def T_tilt(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (0, 1, 0), (0, 0, Z_TILT))

groups = {}
for name, P in PARTS.items():
    if P['group'] != 'none':
        groups.setdefault(P['group'], []).append(name)

IGNORE = {('m_pan_motor', 'm_pan_shaft'), ('m_pan_shaft', '04_pan_hub'), ('m_pan_shaft', '03_tower_cap'), ('m_pan_shaft', '05_tilt_mount'),
          ('m_tilt_shaft', '06_head'), ('m_tilt_shaft', '05_tilt_mount'), ('m_tilt_shaft', 'm_tilt_motor'),
          ('m_tilt_boss', '05_tilt_mount'), ('m_tilt_boss', 'm_tilt_motor'), ('m_tilt_boss', 'm_tilt_shaft'),
          ('m_laser', '06_head'), ('m_camera', '06_head')}      # laser/camera sit in their own bores by design

def overlap(a, b):
    try:
        i = a.intersection(b, engine='manifold')
        return float(abs(i.volume)) if not i.is_empty else 0.0
    except Exception:
        return -1.0

def check(names_a, names_b, Ta, Tb):
    bad = []
    for na in names_a:
        ma = meshes[na].copy(); ma.apply_transform(Ta)
        for nb in names_b:
            if na == nb or (na, nb) in IGNORE or (nb, na) in IGNORE:
                continue
            mb = meshes[nb].copy(); mb.apply_transform(Tb)
            if (ma.bounds[0] > mb.bounds[1]).any() or (mb.bounds[0] > ma.bounds[1]).any():
                continue
            v = overlap(ma, mb)
            if v > 1.0 or v < 0:
                bad.append((na, nb, round(v, 1)))
    return bad

fixed, pan, tilt = groups['fixed'], groups['pan'], groups['tilt']
allp = fixed + pan + tilt
res = {}
st = []
for i, na in enumerate(allp):
    st += check([na], allp[i + 1:], np.eye(4), np.eye(4))
res['static @pan0 tilt0'] = st
for p in (-90, -60, -30, 30, 60, 90):
    res[f'fixed-vs-pan+tilt @pan{p}'] = check(fixed, pan + tilt, np.eye(4), T_pan(p))
for t in (-45, -30, -15, 15, 30, 45):
    res[f'pan-vs-tilt @tilt{t}'] = check(pan, tilt, np.eye(4), T_tilt(t))
    res[f'fixed-vs-tilt @tilt{t}'] = check(fixed, tilt, np.eye(4), T_tilt(t))
report['clearance'] = res
report['clearance_ok'] = all(len(v) == 0 for v in res.values())
allm = trimesh.util.concatenate([meshes[n] for n in allp])
report['assembly_bbox_mm'] = [round(x, 1) for x in (allm.bounds[1] - allm.bounds[0])]
report['tilt_axis_height_mm'] = round(Z_TILT, 2)
report['total_print_grams'] = round(sum(i['grams_petg'] * PARTS[n]['qty'] for n, i in report['parts'].items() if i['printed'] and n != '00_test_coupon'))
hd = meshes['06_head']; cam = meshes['m_camera']; las = meshes['m_laser']
report['head_mass_g'] = round((abs(hd.volume) / 1000 * 0.30 + abs(las.volume) / 1000 * 2.0 * 0 ) * 1.27 + 25 + 10)   # PETG head + ~25 g camera + ~10 g laser
report['steps_per_deg_1_16'] = round(200 * 16 / 360, 2)
with open(os.path.join(ASM_DIR, 'manifest.json'), 'w') as f:
    json.dump({'z_tilt': Z_TILT, 'parts': [{'name': n, 'group': P['group'], 'colour': P['colour'], 'printed': P['printed'], 'note': P['note']} for n, P in PARTS.items() if P['group'] != 'none']}, f, indent=1)
with open(os.path.join(OUT, 'report.json'), 'w') as f:
    json.dump(report, f, indent=1)
print(json.dumps({'clearance_ok': report['clearance_ok'], 'bad': {k: v for k, v in res.items() if v},
                  'grams': report['total_print_grams'], 'bbox': report['assembly_bbox_mm'], 'tilt_axis_z': report['tilt_axis_height_mm'],
                  'parts': {n: (i.get('print_bbox_mm'), i.get('grams_petg')) for n, i in report['parts'].items() if i['printed']}}, indent=1))
