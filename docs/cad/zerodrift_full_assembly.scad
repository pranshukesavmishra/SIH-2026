// ZeroDrift Mk3 — COMPLETE assembly, every item on the BOM
// ========================================================
// Uses parts_lib.scad, which draws each item at its real catalogue
// size. This file only places them.
//
//   xvfb-run -a openscad -D 'view="all"'   -o all.png   --imgsize=2000,1500 zerodrift_full_assembly.scad
//   xvfb-run -a openscad -D 'view="rig"'   -o rig.png   zerodrift_full_assembly.scad
//   xvfb-run -a openscad -D 'view="head"'  -o head.png  zerodrift_full_assembly.scad
//   xvfb-run -a openscad -D 'view="explode"' -o exp.png zerodrift_full_assembly.scad
//
// LAYOUT FINDING, recorded because the model is what surfaced it: the
// 830-point breadboard is 165 mm and the 6-inch acrylic plate is
// 152.4 mm, so the breadboard does NOT fit on the base plate -- it
// overhangs by 12.6 mm. It belongs on the bench beside the rig, which
// is better practice regardless: section 2E deliberately injects
// vibration into that plate, and the control electronics are the last
// thing that should be riding it.

use <parts_lib.scad>
$fn = 72;

TILT_DEG = 12;
PAN_DEG  = 20;


module base_plate() {
    color(C_ACRYLIC, 0.45) difference() {
        translate([-PLATE/2,-PLATE/2,-PLATE_T]) cube([PLATE, PLATE, PLATE_T]);
        cylinder(d = 8, h = 20, center = true);                  // pan shaft
        for (a = [45,135,225,315])                                // motor bolts
            rotate([0,0,a]) translate([31/2,0,0]) cylinder(d = 3.4, h = 20, center = true);
    }
}

include <geometry.scad>

// ---- the rig ------------------------------------------------------
// Split strictly into what is BOLTED TO THE FRAME and what RIDES THE
// PAN SHAFT. An earlier revision had the pan motor body and the
// encoder post inside the pan rotation, which means the post turned
// with the magnet it was supposed to measure -- an encoder that reads
// a constant. The split below is the mechanism, not a drawing choice.
module rig(pan = PAN_DEG, tilt = TILT_DEG) {
    rig_fixed();
    rig_rotating(pan, tilt);
}

// Everything bolted to the frame. The stator is the whole visible
// motor; only the 5 mm shaft turns.
module rig_fixed() {
    base_plate();
    translate([0,0,-PLATE_T]) nema17(shaft_len = 26);
    pan_encoder_arm();
}

// Everything that rides the pan shaft.
//
// PAN TRAVEL IS LIMITED by the fixed encoder arm: past the limit the
// tilt bracket drives into the encoder post. The limit is measured,
// not guessed -- tools/cad/check_clearance.sh sweeps this module
// against rig_fixed() and prints the first angle that touches.
// Firmware soft-limits pan to +-PAN_LIMIT; the benchmark never asks
// for more than +-35.
module rig_rotating(pan = PAN_DEG, tilt = TILT_DEG) {
    rig_pan_deck(pan);
    rig_tilt_group(pan, tilt);
}

// Split again, one level down, because the first split was not enough:
// the head and the pan platform are both carried by the pan shaft, so
// a fixed-vs-rotating test cannot see them collide -- and they do, at
// +21 deg of tilt. Three groups move relative to each other, so all
// three pairs have to be tested.
module rig_pan_deck(pan = PAN_DEG) {
    rotate([0,0,pan]) {
        // platform + DIAMETRIC magnet, magnet centred on the axis
        translate([0,0,PLATFORM_Z]) {
            color("#5b6b7c") cylinder(d = PLATFORM_D, h = PLATFORM_T);
            translate([0,0,PLATFORM_T]) diametric_magnet();
        }

        // tilt stage, sitting ON the platform (underside at its top face)
        //
        // Axis convention, checked numerically rather than by eye after
        // an earlier nesting put the tilt axis along world -Z and the
        // camera looking at the ceiling:
        //   tilt axis = world X,  look = world -Y,  shaft = world X.
        translate([0, 6, TILT_Z]) {
            // riser: four M3 standoffs lifting the bracket off the
            // platform, so the head clears the plate at full tilt
            for (dx = [-42, -20]) for (dy = [-14, 6])
                color(C_BRASS) translate([dx, dy, PLATFORM_Z + PLATFORM_T - TILT_Z])
                    cylinder(d = 5, h = RISER_H, $fn = 6);
            translate([-46, -20, PLATFORM_Z + PLATFORM_T + RISER_H - TILT_Z])
                l_bracket(leg = 30, th = 3, w = 30);
            translate([-40, 0, 0]) rotate([0, 90, 0]) nema17(shaft_len = 22);

            // Tilt encoder. Fixed to the motor side of the joint, so it
            // is outside the rotating group below. The arm reaches UP
            // and back over the shaft: reaching DOWN, as it first did,
            // put the post straight through the pan platform.
            translate([-20, 0, 0]) rotate([0, 90, 0]) {
                color(C_BRASS) translate([-26,0,-4]) cylinder(d = 5, h = 22);
                color("#5b6b7c") translate([-28,-4,TILT_SENS_L]) cube([30, 8, 3]);
                // chip ON the tilt axis (local x = y = 0), AIRGAP away
                translate([0, 0, TILT_SENS_L]) rotate([180,0,0]) as5600();
            }

        }
        // vibration injector, bolted to the moving structure on purpose
        translate([14,-14,PLATFORM_Z + PLATFORM_T]) vibration_motor();
    }
}

// Everything that turns with the TILT shaft.
module rig_tilt_group(pan = PAN_DEG, tilt = TILT_DEG) {
    rotate([0,0,pan]) translate([0, 6, TILT_Z]) rotate([tilt, 0, 0]) {
        // magnet on the shaft end, centred on the tilt axis
        translate([TILT_DISC_X, 0, 0]) rotate([0,90,0]) {
            color("#5b6b7c") cylinder(d = 34, h = TILT_DISC_T);
            translate([0,0,TILT_DISC_T]) diametric_magnet();
        }
        // brass standoff (never printed -- 53 Hz in PLA, on the
        // 47 Hz platform mode; see README) then the head
        color(C_BRASS) rotate([90,0,0]) cylinder(d = 6, h = 42, $fn = 6);
        translate([0, -65, 0]) head();
    }
}

// Fixed pan encoder: short stiff post on the frame, plate reaching in
// over the axis, chip looking DOWN at the magnet from AIRGAP away.
module pan_encoder_arm() {
    color(C_BRASS) translate([PAN_POST_R,0,0]) cylinder(d = 5, h = PAN_SENS_Z + 3);
    color("#5b6b7c") translate([-6,-5,PAN_SENS_Z]) cube([PAN_POST_R + 12, 10, 3]);
    translate([0,0,PAN_SENS_Z]) rotate([180,0,0]) as5600();
}

// ---- the head: webcam board + laser + filter in the ABS box -------
// Sized to its contents, and the sizing was wrong twice before it was
// right. A de-housed webcam PCB is 32 mm square, so a 30 mm-tall box
// cannot hold it -- the board poked through the floor and lid. And the
// lens must point OUT through the front face; the first placement had
// it aimed into the box's own interior. Both are the sort of thing you
// only see once the parts are drawn at real size next to each other.
//
//   72 x 46 x 42   box
//   32 x 32        webcam PCB, lens barrel 12 dia x 9 long
//   6.5 x 18       KY-008 brass barrel, boresighted parallel
HEAD_W = 72; HEAD_D = 46; HEAD_H = 42;

module head(walls = true) {
    if (walls)
        translate([-HEAD_W/2, -HEAD_D/2, -HEAD_H/2])
            abs_box(HEAD_W, HEAD_D, HEAD_H);
    else                                   // detail view: frame only
        color("#d9822b", 0.9)
            for (x = [-HEAD_W/2, HEAD_W/2], y = [-HEAD_D/2, HEAD_D/2])
                translate([x, y, -HEAD_H/2]) cylinder(d = 1.2, h = HEAD_H, $fn = 10);

    // rotate([90,0,0]) sends a part's local +Z (its optical axis) to
    // world -Y, which is the direction the head looks.
    // Board at y = -14 puts the 9 mm lens barrel flush with the front
    // face at y = -23, where its clearance hole is.
    translate([-16, -14, 0]) rotate([90,0,0]) {
        webcam_board();
        translate([0,0,10.6]) red_filter(22);
    }
    // laser barrel is 18 mm, so its face sits at y = -5 to finish flush
    translate([20, -5, -2]) rotate([90,0,0]) ky008_laser();

    // Service loop: slack enough for full travel, never in tension, and
    // it has to STAY ABOVE THE BASE PLATE. The first routing dropped to
    // z = -4 in world coordinates -- i.e. the camera's own cable ran
    // through the 3 mm acrylic it is bolted to. Invisible in every
    // render; the clearance sweep found it at the neutral pose.
    wire_run([[-30,12,-10],[-46,20,-22],[-48,6,-30],[-38,-6,-36]], 3.0);
}

// ---- the bench: electronics that do NOT ride the plate -------------
module bench_electronics() {
    // breadboard beside the rig -- it is 165 mm and the plate is 152.4
    translate([-190, -28, 0]) {
        breadboard();
        translate([40, 27, 10]) arduino_nano_usbc();
        translate([100, 38, 10]) a4988();
        translate([100, 14, 10]) a4988();
        translate([140, 27, 10]) tca9548a();
        translate([78, 40, 10]) cap100uf();
        translate([78, 12, 10]) cap100uf();
    }
    // 12 V pack and its switched feed
    translate([-200, 80, 0]) pack_18650_3s();
    translate([-120, 74, 0]) barrel_to_screw();
    translate([-90, 74, 12]) toggle_switch();

    // looms: battery -> switch -> drivers, and drivers -> motors
    wire_run([[-125,88,6],[-105,80,10],[-92,76,4]], 2.6, "#b03030");
    wire_run([[-90,66,2],[-70,50,4],[-60,22,10]], 2.6, "#b03030");
    wire_run([[-60,20,12],[-40,6,14],[-14,-6,10]], 2.4, "#2f6fb5");
    wire_run([[-150,0,12],[-110,-20,10],[-70,-26,8],[-30,-18,6]], 2.4);
}

// ---- beacon and decoy, the targets across the room ------------------
module beacon_unit() {
    abs_box(90, 60, 40);
    translate([45, 30, 40]) { led_10mm("#e03131"); translate([0,0,14]) pingpong_ball(); }
    translate([16, 12, 40]) arduino_nano_usbc();
    translate([74, 14, 40]) toggle_switch();
}
module decoy_unit() {
    abs_box(70, 55, 26);
    translate([35, 27, 26]) led_10mm("#f1f3f5");
    translate([6, 4, -16]) aa_holder_3();
    translate([58, 12, 26]) toggle_switch();
}

module scene_targets() {
    // Targets sit across the room in reality; placed here at a scale
    // that keeps one readable image. The beacon is what the tracker
    // must find (4 Hz blink); the decoy is the steady white light it
    // must refuse.
    translate([95, 150, 0]) rotate([0,0,-150]) beacon_unit();
    translate([205, 118, 0]) rotate([0,0,-145]) decoy_unit();
}

module desk() {
    color(C_DESK) translate([-290,-120,-PLATE_T-40]) cube([540, 320, 34]);
}

// ---- views ----------------------------------------------------------
module view_all()  { desk(); rig(); bench_electronics(); scene_targets(); }
module view_rig()  { rig(); }
module view_head() { head(); }
// Exploded, in build order, bottom to top -- the same order as
// TERMINAL_MK3.md section 3's stages, so the picture and the procedure
// agree. Labelled, because an exploded view without names is half a
// diagram.
module label(txt, sz = 9) {
    color("#1b1f24") rotate([72,0,30])
        linear_extrude(0.6) text(txt, size = sz, font = "DejaVu Sans:style=Bold");
}

module view_explode() {
    // 1 - pan motor, bolts to the plate UNDERSIDE
    translate([0,0,-95]) { nema17(shaft_len = 30); translate([70,0,10]) label("1  NEMA17 pan"); }

    // 2 - acrylic base plate, shaft clearance hole + 31 mm bolt circle
    base_plate();
    translate([95,0,0]) label("2  acrylic base, 3 mm");

    // 3 - platform + diametric magnet on the rotation axis
    translate([0,0,62]) {
        color("#5b6b7c") cylinder(d = PLATFORM_D, h = PLATFORM_T);
        translate([0,0,PLATFORM_T]) diametric_magnet();
        translate([70,0,0]) label("3  platform + DIAMETRIC magnet");
    }
    // 4 - AS5600 on its fixed arm: chip CONCENTRIC with the axis, and
    //     AIRGAP (1.5 mm) above the magnet face. Off-axis it reads noise.
    translate([0,0,92]) {
        color(C_BRASS) translate([PAN_POST_R,0,-30]) cylinder(d = 5, h = 30);
        color("#5b6b7c") translate([-6,-5,0]) cube([PAN_POST_R + 12, 10, 3]);
        rotate([180,0,0]) as5600();
        translate([PAN_POST_R + 26,0,0]) label("4  AS5600 on the axis, 1.5 mm gap");
    }

    // 4b - the 14 mm standoff riser. Not decoration: without it the
    //      head reaches the base plate at +17 deg of tilt.
    translate([0,0,126]) {
        for (dx = [-11, 11]) for (dy = [-10, 10])
            color(C_BRASS) translate([dx, dy, 0]) cylinder(d = 5, h = RISER_H, $fn = 6);
        translate([70,0,0]) label("5  14 mm riser — buys full tilt travel");
    }

    // 5 - L-bracket carrying the tilt stage
    translate([-54,-17,158]) { l_bracket(); translate([-96,0,10]) label("6  L-bracket"); }

    // 7 - tilt motor, shaft horizontal
    translate([0,0,202]) { rotate([-90,0,0]) nema17(); translate([78,0,0]) label("7  NEMA17 tilt"); }

    // 8 - metal standoff (never printed -- 53 Hz resonance in PLA)
    translate([0,0,252]) { color(C_BRASS) cylinder(d = 6, h = 42, $fn = 6);
                           translate([56,0,20]) label("8  M3 BRASS standoff"); }

    // 9 - head: webcam + red filter + laser
    translate([0,0,324]) { head(); translate([78,0,0]) label("9  head: webcam + filter + laser"); }
}

view = "all";
if      (view == "all")     view_all();
else if (view == "rig")     view_rig();
else if (view == "head")    view_head();
else if (view == "explode") view_explode();
