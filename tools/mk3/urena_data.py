"""Plan Urena: the words and numbers shared by the build page, the Plan PDF and the print-shop sheet.

Numbers that come from the CAD (grams, sizes, belt maths) are read from tools/mk3/out/report.json,
so run tools/mk3/mk3_cad.py first. Prices are estimates in rupees (low, high); check in the shop.
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT = json.load(open(os.path.join(ROOT, 'out', 'report.json')))
P = REPORT['params']
BELTS = REPORT['belts']

# ---------------------------------------------------------------- printed parts, in build order
# name: (plain name, what it does, qty, colour, supports, note)
PRINT = [
    ('00_test_coupon', 'Test coupon', 'Checks the fits before anything big is printed: both bearing pockets, both bearing pins, an M3 nut and a screw hole.', 1, 'Any', 'None', 'PRINT THIS FIRST. We check it before the rest.'),
    ('01_base_hub', 'Base hub', 'Holds the two big pan bearings and the pan motor. The cables come out of a hole at the bottom.', 1, 'Grey', 'Only inside the motor pocket', 'Biggest part. Use a brim.'),
    ('02_leg_1', 'Leg', 'Three legs make a stable tripod. Bolt into the base hub.', 3, 'Grey', 'None', 'Print 3 (files 02_leg_1, _2, _3 are the same leg).'),
    ('03_pan_sensor_bridge', 'Pan sensor bridge', 'Holds the pan sensor board just above the pan motor shaft.', 1, 'Grey', 'None', ''),
    ('04_magnet_cap', 'Magnet cap', 'Sits on the pan motor shaft tip and holds the small round magnet dead centre.', 1, 'Any', 'None', 'Tiny: print 2 (one spare).'),
    ('05_spindle_washer', 'Spindle washer', 'Three screws pull it up against the lower bearing so the pan has no play.', 1, 'Any', 'None', ''),
    ('06_pan_turntable', 'Pan turntable', 'The hollow tube, the 80-tooth pulley and the round deck, all in one print.', 1, 'Grey', 'None', 'Print deck-down (the file is already turned).'),
    ('07_arm_right', 'Right arm', 'Holds the right tilt bearing. The tilt pulley turns just inside it; the tilt sensor bracket screws to its outside.', 1, 'Grey', 'None', ''),
    ('08_arm_left', 'Left arm', 'Holds the left tilt bearing. The cables leave the head on this side.', 1, 'Grey', 'None', ''),
    ('09_tilt_motor_plate', 'Tilt motor stand', 'Stands on the deck under the head and holds the tilt motor. Slots let the motor slide to tighten the belt.', 1, 'Grey', 'None', ''),
    ('10_tilt_sensor_bracket', 'Tilt sensor bracket', 'Screws to the outside of the right arm and holds the tilt sensor facing the magnet in the trunnion end.', 1, 'Grey', 'None', ''),
    ('11_head', 'Head', 'The box that carries the camera and the laser. Open top for easy wiring.', 1, 'Black', 'None', 'Black stops stray light.'),
    ('12_front_plate', 'Front plate', 'The camera board screws to this. Slots fit 28 to 34 mm hole patterns.', 1, 'Black', 'None', ''),
    ('13_laser_holder', 'Laser holder', 'Tube for a 12 mm laser, with 3 screws to aim it exactly at the camera centre.', 1, 'Black', 'None', ''),
    ('14_trunnion_left', 'Left trunnion', 'Hollow tube bolted to the head. Turns in the left bearing. Cables pass through it.', 1, 'Grey', 'None', ''),
    ('15_trunnion_right', 'Right trunnion + tilt pulley', 'One print: bolts to the head, the 80-tooth tilt pulley, then the tube that turns in the right bearing. The tilt magnet sits in its end.', 1, 'Grey', 'None', ''),
    ('16_electronics_box', 'Electronics box', 'Holds the Arduino UNO + CNC shield. Power jack, fuse and switch on the wall.', 1, 'Dark grey', 'None', 'Use a brim.'),
    ('17_electronics_lid', 'Box lid', 'Lid with a 40 mm fan over the motor drivers.', 1, 'Dark grey', 'None', ''),
]

def part(name):
    return REPORT['parts'][name]

def print_rows():
    rows = []
    for name, title, what, qty, colour, supports, note in PRINT:
        p = part(name)
        rows.append(dict(name=name, title=title, what=what, qty=qty, colour=colour, supports=supports, note=note,
                         bbox=p['print_bbox_mm'], grams=p['grams_petg'], img=name if not name.startswith('02_leg') else '02_leg'))
    return rows

def total_grams():
    return round(sum(r['grams'] * (r['qty'] if r['name'] != '02_leg_1' else 3) for r in print_rows()))

# ---------------------------------------------------------------- buy list
# group -> list of (item, qty, (low, high) each, where, alternative / note)
AMAR, BEAR, HW, ONL = 'Amar Robotics', 'Bearing shop', 'Hardware shop', 'Online (Robu / Amazon)'
BUY = [
    ('Bearings, belts, pulleys', 'The moving parts. Take the test coupon and the printed pins to the bearing shop.', [
        ('6808-2RS bearing (40 x 52 x 7 mm)', 2, (150, 250), BEAR, '6808-ZZ is the same size (metal shields). Any brand.'),
        ('6806-2RS bearing (30 x 42 x 7 mm)', 2, (120, 200), BEAR, '6806-ZZ is the same size.'),
        ('GT2 pulley, 20 teeth, 5 mm bore, for 6 mm belt', 3, (80, 150), AMAR, '1 spare. Metal (aluminium), with 2 grub screws.'),
        ('GT2 closed belt 6 mm wide, 232 mm', 2, (80, 150), ONL, '1 spare. 240 mm also fits (anything 227 to 245 mm).'),
        ('GT2 closed belt 6 mm wide, 280 mm', 2, (80, 160), ONL, '1 spare. 276 to 284 mm fits.'),
    ]),
    ('Controller and power', 'No breadboard. Everything plugs into the CNC shield.', [
        ('Arduino UNO R3 (CH340 clone is fine) + USB-B cable', 2, (450, 700), AMAR, '1 spare. The MK2 Nano is a third backup.'),
        ('CNC Shield V3 (for UNO)', 2, (250, 350), AMAR, '1 spare. Must say "V3" and fit on an UNO.'),
        ('A4988 driver with heatsink', 2, (150, 200), AMAR, 'Spares. Reuse the 2 from MK2 if they still work.'),
        ('12 V 5 A adapter (SMPS), 5.5 x 2.1 mm plug', 1, (450, 650), AMAR, '12 V 3 A is the minimum. Not a 12 V 1 A phone-style one.'),
        ('Panel DC jack 5.5 x 2.1 mm (female, with nut)', 1, (30, 50), AMAR, 'Screws into the box wall.'),
        ('Fuse holder (5 x 20 mm) + 3 A fuses', 1, (40, 80), AMAR, 'Buy a pack of 5 fuses.'),
        ('Rocker switch (KCD1, 6 A)', 1, (20, 40), AMAR, 'Any 2-pin ON/OFF switch rated 3 A or more.'),
        ('Silicone wire 18 AWG, red + black', 2, (50, 80), AMAR, '1 m of each colour. For the 12 V only.'),
        ('40 mm fan, 12 V', 1, (80, 120), AMAR, 'Cools the two drivers.'),
        ('MOSFET switch module (D4184 / AOD4184)', 1, (60, 90), AMAR, 'Switches the vibration motor. A 2N2222 + diode from the MK2 kit also works.'),
        ('Dupont jumper cables, female-female, 20 cm', 1, (60, 100), AMAR, 'One pack of 40. For the sensors.'),
        ('Spiral cable wrap, 1 m', 1, (30, 60), HW, 'Keeps the cable bundle neat.'),
    ]),
    ('Laser and magnets', '', [
        ('12 mm laser module, 650 nm red, 5 mW, 5 V', 2, (100, 200), AMAR, '1 spare. Only 5 mW (Class 2/3R). Never a "burning" laser.'),
        ('Diametric magnet 6 x 2.5 mm (AS5600 type)', 2, (30, 60), ONL, 'Spares. One usually comes with each AS5600 board.'),
    ]),
    ('Screws and small things', 'Buy an M3 kit; the counts are in the table on the "Assemble" page.', [
        ('M3 screw kit (6 to 30 mm) with nuts and washers', 1, (250, 400), HW, ''),
        ('M3 x 35 mm screws', 4, (5, 10), HW, 'For the pan sensor bridge (2 + 2 spare).'),
        ('M4 x 30 mm bolts + nuts', 6, (8, 15), HW, 'Legs.'),
        ('M4 x 20 mm bolts + nuts + washers', 8, (6, 12), HW, 'Arms to the deck.'),
        ('M2.5 x 6 mm screws', 6, (5, 10), HW, 'Sensor boards. M2 x 6 self-tapping also works.'),
        ('Super glue (CA)', 1, (30, 60), HW, 'One drop fixes the magnet cap.'),
    ]),
]

PRINT_COST_PER_G = (5, 10)          # rupees per gram at a local print shop (ask for a quote)

def buy_totals():
    lo = sum(q * p[0] for _, _, items in BUY for (_, q, p, _, _) in items)
    hi = sum(q * p[1] for _, _, items in BUY for (_, q, p, _, _) in items)
    return lo, hi

def print_cost():
    g = total_grams()
    return g * PRINT_COST_PER_G[0], g * PRINT_COST_PER_G[1]

# ---------------------------------------------------------------- reuse from MK2
REUSE = [
    ('2 x NEMA17 motors + their cables', 'Yes', 'Same motors, same 4-pin cables.'),
    ('2 x A4988 drivers', 'Test first', 'Plug each into the CNC shield and run the self-test. If one burned with the breadboard, use a spare.'),
    ('2 x AS5600 sensors + magnets', 'Yes', 'Pan sensor now reads the pan motor shaft; tilt sensor reads the end of the right trunnion.'),
    ('TCA9548A sensor splitter', 'Yes', 'Still needed: both AS5600s have the same address.'),
    ('USB camera', 'Yes', 'Works as it is. See "Camera" for a sharper option.'),
    ('KY-008 laser', 'Backup', 'The head is made for a 12 mm tube laser. Keep the KY-008 as a spare.'),
    ('Vibration motor + transistor kit', 'Yes', 'Or use the MOSFET module.'),
    ('Arduino Nano', 'Spare board', 'The MK3 firmware also runs on the Nano (set BOARD_CNC_SHIELD to 0).'),
    ('Beacon + decoy', 'Yes', 'No change.'),
    ('Laptop software + Live page', 'Yes', 'Pick "Both belts 20T→80T (4:1)" in the drive menu.'),
    ('12 V 2 A adapter', 'Tests only', 'Too weak for two motors at full speed, and its wire was damaged. Keep it for bench tests of one motor.'),
    ('Breadboard, acrylic, L-brackets, couplings, servo', 'No', 'Not needed any more.'),
]

# ---------------------------------------------------------------- cameras
CAMERAS = [
    ('Keep the MK2 USB camera', 'Free', '1280 px across about 70°', 70, 1280, 'Works today. Nothing to buy.', 'ok'),
    ('USB 1080p camera board with M12 lens mount (OV2710 or IMX291) + 6 mm M12 lens', '₹1,800–3,500 + lens ₹300–600',
     '1920 px across about 51°', 51, 1920, 'Recommended upgrade: about 2× finer aim. The 38 × 38 mm board fits the front plate. Online (Amazon: "USB camera module 1080p M12").', 'best'),
    ('Logitech C270', '₹1,300–1,700', '1280 px across about 55°', 55, 1280, 'Easy to find locally. A little better than a basic webcam. Mount with a strap, not the front plate.', 'ok'),
    ('ESP32-CAM, OV7670, Raspberry Pi camera', '—', '—', 0, 0, 'Not recommended: Wi-Fi delay, low quality, or needs a Raspberry Pi.', 'no'),
]

def deg_per_px(fov, px):
    return fov / px if px else 0

# ---------------------------------------------------------------- pins (UNO + CNC Shield V3)
PINS = [
    ('D2 / D5', 'X.STEP / X.DIR', 'Pan driver (X socket)'),
    ('D3 / D6', 'Y.STEP / Y.DIR', 'Tilt driver (Y socket)'),
    ('D8', 'EN', 'Both drivers on/off (LOW = on)'),
    ('D12', 'SpnEn', 'Laser signal'),
    ('D13', 'SpnDir', 'Vibration motor (through the MOSFET module)'),
    ('A4 / A5', 'SDA / SCL', 'TCA9548A splitter → both AS5600 sensors'),
    ('5V / GND', '5V / GND', 'Sensors, splitter, laser, MOSFET module'),
    ('12 V terminal', 'blue screw terminal', 'From the ON/OFF switch (red +, black −)'),
]

# ---------------------------------------------------------------- screws per step
SCREWS = [
    ('Legs → base hub', 'M4 × 30 + nut', 6),
    ('Pan motor → base hub (front 2)', 'M3 × 8', 2),
    ('Pan motor + sensor bridge (back 2)', 'M3 × 35', 2),
    ('Spindle washer → turntable', 'M3 × 12', 3),
    ('Arms → deck', 'M4 × 20 + nut + washer', 8),
    ('Left trunnion → head', 'M3 × 10 + nut', 3),
    ('Right trunnion → head (from inside the head)', 'M3 × 12', 3),
    ('Tilt motor → its stand', 'M3 × 10', 4),
    ('Tilt motor stand → deck', 'M4 × 16 + nut', 2),
    ('Tilt sensor bracket → right arm', 'M3 × 12', 2),
    ('Front plate → head', 'M3 × 12', 3),
    ('Camera board → front plate', 'M2 or M3 × 8 + nut', 4),
    ('Laser aiming screws', 'M3 × 8', 3),
    ('AS5600 boards', 'M2.5 × 6', 4),
    ('UNO → box', 'M3 × 6', 4),
    ('Fan → lid', 'M3 × 12', 4),
    ('Lid → box', 'M3 × 10', 4),
]
