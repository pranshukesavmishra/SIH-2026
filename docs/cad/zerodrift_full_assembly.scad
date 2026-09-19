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

PLATE = 152.4;      // 6 inch acrylic, as bought
PLATE_T = 3;
TILT_DEG = 12;
PAN_DEG  = 20;

C_ACRYLIC = "#cfe3ee"; C_WIRE = "#2f3336"; C_DESK = "#e9e6e0";
C_BRASS = "#b08d57";

module base_plate() {
    color(C_ACRYLIC, 0.45) difference() {
        translate([-PLATE/2,-PLATE/2,-PLATE_T]) cube([PLATE, PLATE, PLATE_T]);
        cylinder(d = 8, h = 20, center = true);                  // pan shaft
        for (a = [45,135,225,315])                                // motor bolts
            rotate([0,0,a]) translate([31/2,0,0]) cylinder(d = 3.4, h = 20, center = true);
    }
}

// ---- the rig ------------------------------------------------------
module rig() {
    base_plate();

    rotate([0,0,PAN_DEG]) {
        // pan motor hangs below, face bolted to the plate underside,
        // shaft up through the clearance hole
        translate([0,0,-PLATE_T]) nema17(shaft_len = 26);

        // pan encoder: magnet on the rotating platform, AS5600 on a
        // FIXED arm (single-shaft mounting -- these motors have no
        // rear shaft; see TERMINAL_MK3.md section 6)
        translate([0,0,23]) {
            color("#5b6b7c") cylinder(d = 34, h = 3);
            translate([0,0,3]) diametric_magnet();
        }
        color(C_BRASS) translate([26,0,0]) cylinder(d = 5, h = 30);   // fixed post
        color("#5b6b7c") translate([26,0,29]) rotate([0,0,180])
            translate([0,-3,0]) cube([18,6,3]);
        translate([12,0,30.5]) rotate([180,0,0]) as5600();

        // tilt stage on the pan platform
        translate([-21, 8, 26]) {
            l_bracket(leg = 34, th = 3);
            translate([21, 34, 17]) rotate([-90,0,0]) {
                nema17(shaft_len = 22);
                translate([0,0,22]) { color("#5b6b7c") cylinder(d = 34, h = 3);
                                      translate([0,0,3]) diametric_magnet(); }
                color(C_BRASS) translate([26,0,0]) cylinder(d = 5, h = 26);
                translate([12,0,27]) rotate([180,0,0]) as5600();

                // METAL standoff to the head -- never printed, see the
                // resonance table in TERMINAL_MK3.md section 6 (a PLA
                // one lands at 53 Hz, on the 47 Hz platform mode)
                translate([0,0,25]) rotate([0,TILT_DEG,0]) {
                    color(C_BRASS) cylinder(d = 6, h = 42, $fn = 6);
                    translate([0,0,42]) head();
                }
            }
        }
        // vibration injector, bolted to the moving structure on purpose
        translate([14,-14,26.5]) vibration_motor();
    }
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

    // service loop: slack enough for full travel, never in tension
    wire_run([[-30,12,-10],[-46,20,-22],[-50,6,-40],[-34,-8,-52]], 3.0);
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
        color("#5b6b7c") cylinder(d = 34, h = 3);
        translate([0,0,3]) diametric_magnet();
        translate([70,0,0]) label("3  platform + DIAMETRIC magnet");
    }
    // 4 - AS5600 on its fixed arm, 0.5-3 mm above the magnet
    translate([62,0,86]) { rotate([180,0,0]) as5600(); translate([28,0,0]) label("4  AS5600 (fixed arm)"); }

    // 5 - L-bracket carrying the tilt stage
    translate([-54,-17,118]) { l_bracket(); translate([-96,0,10]) label("5  L-bracket"); }

    // 6 - tilt motor, shaft horizontal
    translate([0,0,165]) { rotate([-90,0,0]) nema17(); translate([78,0,0]) label("6  NEMA17 tilt"); }

    // 7 - metal standoff (never printed -- 53 Hz resonance in PLA)
    translate([0,0,228]) { color("#b08d57") cylinder(d = 6, h = 42, $fn = 6);
                           translate([56,0,20]) label("7  M3 BRASS standoff"); }

    // 8 - head: webcam + red filter + laser
    translate([0,0,300]) { head(); translate([78,0,0]) label("8  head: webcam + filter + laser"); }
}

view = "all";
if      (view == "all")     view_all();
else if (view == "rig")     view_rig();
else if (view == "head")    view_head();
else if (view == "explode") view_explode();
