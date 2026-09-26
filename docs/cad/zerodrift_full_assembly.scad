// ZeroDrift MK2 — COMPLETE assembly, as built from the picture guide
// ===================================================================
// Uses parts_lib.scad, which draws each item at its real catalogue
// size. This file only places them.
//
//   xvfb-run -a openscad -D 'view="all"'   -o all.png   --imgsize=2000,1500 zerodrift_full_assembly.scad
//   xvfb-run -a openscad -D 'view="rig"'   -o rig.png   zerodrift_full_assembly.scad
//   xvfb-run -a openscad -D 'view="explode"' -o exp.png zerodrift_full_assembly.scad
//
// The rig is the one in docs/submission/picture_guide_source.html:
// NO COUPLER. The big disc is glued straight onto the pan shaft with a
// ring of M-Seal under it, the magnet is superglued onto the 2 mm of
// shaft tip left clean on top, three M3 x 40 stilts carry the
// L-bracket over the sensor arm, and the head box is screwed flat and
// centred on a small disc glued the same way onto the tilt shaft.
// Every dimension comes from geometry.scad.
//
// LAYOUT FINDING, kept from the first model: the 830-point breadboard
// is 165 mm and the base is 152.4 mm, so the breadboard lives on the
// bench beside the rig, not on the base.

use <parts_lib.scad>
include <geometry.scad>
$fn = 72;

TILT_DEG = 12;
PAN_DEG  = 20;

// ---- fasteners -----------------------------------------------------
// M3 screw, head DOWN at the origin, shank up +Z (flip with mirror).
module m3_screw(len) {
    color(C_STEEL) { translate([0,0,-2.4]) cylinder(d = 5.5, h = 2.4); cylinder(d = 3, h = len, $fn = 16); }
}
module m3_nut() { color(C_STEEL) cylinder(d = 6.4, h = NUT_H, $fn = 6); }

// ---- one module per physical piece, in its FINAL position ----------
// World coordinates at pan = 0 and tilt = 0. The kinematic groups
// below and the per-part web export both use exactly these, so the
// clearance sweep and the 3D page cannot disagree about the rig.

// A  base, 15 cm square: LOOSE 8 mm middle hole, the 4 motor holes on
// the 31 mm square, and one hole for the sensor-arm post.
module base_plate() {
    color(C_ACRYLIC, 0.45) difference() {
        translate([-PLATE/2,-PLATE/2,-PLATE_T]) cube([PLATE, PLATE, PLATE_T]);
        cylinder(d = BASE_HOLE_D, h = 20, center = true);
        for (a = [45,135,225,315])
            rotate([0,0,a]) translate([31/2,0,0]) cylinder(d = 3.4, h = 20, center = true);
        translate([PAN_POST_R,0,0]) cylinder(d = 3.4, h = 20, center = true);
    }
}
// Four legs, taller than the hanging motor, so it never touches the table.
module base_legs() {
    color("#c79e6e") for (sx = [-1,1], sy = [-1,1])
        translate([sx*(PLATE/2 - LEG_W/2 - 3) - LEG_W/2, sy*(PLATE/2 - LEG_W/2 - 3) - LEG_W/2, -PLATE_T - LEG_H])
            cube([LEG_W, LEG_W, LEG_H]);
}
// Bottom (pan) motor hanging under the base, shaft up through the hole.
module pan_motor() { translate([0,0,PAN_FACE_Z]) nema17(shaft_len = SHAFT_L); }
// 4 x M3 x 16 down through the base, 2 nuts on each as spacers.
module pan_motor_screws() {
    for (a = [45,135,225,315]) rotate([0,0,a]) translate([31/2,0,0]) {
        translate([0,0,2.4]) mirror([0,0,1]) m3_screw(16);
        for (z = [-PLATE_T - NUT_H, -PLATE_T - 2*NUT_H]) translate([0,0,z]) m3_nut();
    }
}
// B  big disc: tight 5 mm middle hole, 3 small stilt holes on ONE side.
module platform() {
    color(C_ACRYLIC, 0.6) translate([0,0,PLATFORM_Z]) difference() {
        cylinder(d = PLATFORM_D, h = PLATFORM_T);
        cylinder(d = 5, h = 20, center = true);
        for (a = STILT_ANG) rotate([0,0,a]) translate([STILT_R,0,0]) cylinder(d = 3.4, h = 20, center = true);
    }
}
// Fat M-Seal ring UNDER the disc, all round the shaft. Never touching the base.
module platform_glue() {
    color("#8e9170") translate([0,0,PLATFORM_Z - GLUE_H]) difference() {
        cylinder(d1 = GLUE_D * 0.7, d2 = GLUE_D, h = GLUE_H);
        cylinder(d = 5, h = 40, center = true);
    }
}
// Diametric magnet on the clean shaft TIP: north half and south half,
// so the page can colour the poles across the diameter.
module pan_magnet(half = "n") {
    translate([0,0,PAN_TIP_Z]) intersection() {
        cylinder(d = MAGNET_D, h = MAGNET_H);
        translate([half == "n" ? -MAGNET_D : 0, -MAGNET_D, -1]) cube([MAGNET_D, 2*MAGNET_D, MAGNET_H + 2]);
    }
}
// Sensor-arm post: M3 x 40 up through the base, locked with a nut, and
// a nut under and over the strip to set its height. It NEVER turns.
module pan_post() {
    translate([PAN_POST_R,0,-PLATE_T]) m3_screw(POST_L);
    translate([PAN_POST_R,0,0]) m3_nut();
    translate([PAN_POST_R,0,PAN_SENS_Z - NUT_H]) m3_nut();
    translate([PAN_POST_R,0,PAN_SENS_Z + STRIP_T]) m3_nut();
}
// D  strip 1.5 x 6 cm, hole at one end on the post, far end over the axis.
module pan_strip() {
    color(C_ACRYLIC, 0.6) difference() {
        translate([PAN_POST_R + 3 - STRIP_L, -STRIP_W/2, PAN_SENS_Z]) cube([STRIP_L, STRIP_W, STRIP_T]);
        translate([PAN_POST_R,0,0]) cylinder(d = 3.4, h = 200, center = true);
    }
}
// AS5600 under the strip, chip DOWN, on the axis, AIRGAP over the magnet.
module pan_sensor() { translate([0,0,PAN_SENS_Z]) rotate([180,0,0]) as5600(); }
// 3 stilts: M3 x 40 pushed UP through the big disc on the side away
// from the sensor arm. Nut on the disc; nut under and over the foot.
module stilts() {
    for (a = STILT_ANG) rotate([0,0,a]) translate([STILT_R,0,0]) {
        translate([0,0,PLATFORM_Z]) m3_screw(STILT_L);
        translate([0,0,PLATFORM_Z + PLATFORM_T]) m3_nut();
        translate([0,0,FOOT_Z - NUT_H]) m3_nut();
        translate([0,0,FOOT_Z + FOOT_T]) m3_nut();
    }
}
// L-bracket: flat foot on the stilts, standing leg the tilt motor bolts to.
module bracket() {
    color("#9aa3ae") difference() {
        union() {
            translate([FOOT_X0, -BRACKET_W/2, FOOT_Z]) cube([LEG_X + BRACKET_T - FOOT_X0, BRACKET_W, FOOT_T]);
            translate([LEG_X, -BRACKET_W/2, FOOT_Z]) cube([BRACKET_T, BRACKET_W, TILT_Z + 24 - FOOT_Z]);
        }
        for (a = STILT_ANG) rotate([0,0,a]) translate([STILT_R,0,0]) cylinder(d = 3.4, h = 400, center = true);
        translate([0, TILT_Y, TILT_Z]) rotate([0,90,0]) {
            cylinder(d = 23, h = 400, center = true);                   // boss + shaft
            for (a = [45,135,225,315]) rotate([0,0,a]) translate([31/2,0,0]) cylinder(d = 3.4, h = 400, center = true);
        }
    }
}
// Top (tilt) motor, face on the standing leg, shaft pointing SIDEWAYS (+X).
module tilt_motor() { translate([LEG_X, TILT_Y, TILT_Z]) rotate([0,90,0]) nema17(shaft_len = SHAFT_L); }
// 4 x M3 x 6 through the leg into the motor face.
module tilt_motor_screws() {
    translate([LEG_X + BRACKET_T, TILT_Y, TILT_Z]) rotate([0,90,0])
        for (a = [45,135,225,315]) rotate([0,0,a]) translate([31/2,0,0])
            translate([0,0,2.4]) mirror([0,0,1]) m3_screw(6);
}
// C  small disc: tight middle hole, 2 small holes for the head screws.
module tilt_disc() {
    color(C_ACRYLIC, 0.6) translate([TILT_DISC_X, TILT_Y, TILT_Z]) rotate([0,90,0]) difference() {
        cylinder(d = TILT_DISC_D, h = TILT_DISC_T);
        cylinder(d = 5, h = 20, center = true);
        for (s = [-1,1]) translate([0, s*13, 0]) cylinder(d = 3.4, h = 20, center = true);
    }
}
// Same M-Seal ring, on the motor side of the small disc, clear of the bracket.
module tilt_glue() {
    color("#8e9170") translate([TILT_DISC_X - GLUE_H, TILT_Y, TILT_Z]) rotate([0,90,0]) difference() {
        cylinder(d1 = GLUE_D * 0.6, d2 = GLUE_D * 0.85, h = GLUE_H);
        cylinder(d = 5, h = 40, center = true);
    }
}
// The head box, FLAT on the small disc and CENTRED on the tilt axis,
// so it balances. Holes: shaft tip (back), camera window + laser (front).
CAM_X   = HEAD_X - CAM_LASER/2;
LASER_X = HEAD_X + CAM_LASER/2;
module head_box() {
    color("#d9822b", 0.25) difference() {
        translate([HEAD_X - HEAD_W/2, TILT_Y - HEAD_D/2, TILT_Z - HEAD_H/2]) cube([HEAD_W, HEAD_D, HEAD_H]);
        translate([HEAD_X - HEAD_W/2 + 2, TILT_Y - HEAD_D/2 + 2, TILT_Z - HEAD_H/2 + 2]) cube([HEAD_W - 4, HEAD_D - 4, HEAD_H - 4]);
        translate([HEAD_X - HEAD_W/2, TILT_Y, TILT_Z]) rotate([0,90,0]) cylinder(d = 8, h = 10, center = true);
        translate([CAM_X - 8, TILT_Y - HEAD_D/2 - 1, TILT_Z - 8]) cube([16, 4, 16]);
        translate([LASER_X, TILT_Y - HEAD_D/2, TILT_Z]) rotate([90,0,0]) cylinder(d = 7.5, h = 10, center = true);
    }
}
// Webcam board behind the window and the laser 2 cm beside it, both
// looking the same way (world -Y), so the camera sees its own dot.
module head_camera() { translate([CAM_X, TILT_Y - 14, TILT_Z]) rotate([90,0,0]) webcam_board(); }
module head_laser()  { translate([LASER_X, TILT_Y - 5, TILT_Z]) rotate([90,0,0]) ky008_laser(); }

module piece(which) {
    if      (which == "base")              base_plate();
    else if (which == "base_legs")         base_legs();
    else if (which == "pan_motor")         pan_motor();
    else if (which == "pan_motor_screws")  pan_motor_screws();
    else if (which == "platform")          platform();
    else if (which == "platform_glue")     platform_glue();
    else if (which == "pan_magnet_n")      pan_magnet("n");
    else if (which == "pan_magnet_s")      pan_magnet("s");
    else if (which == "pan_post")          pan_post();
    else if (which == "pan_strip")         pan_strip();
    else if (which == "pan_sensor")        pan_sensor();
    else if (which == "stilts")            stilts();
    else if (which == "bracket")           bracket();
    else if (which == "tilt_motor")        tilt_motor();
    else if (which == "tilt_motor_screws") tilt_motor_screws();
    else if (which == "tilt_disc")         tilt_disc();
    else if (which == "tilt_glue")         tilt_glue();
    else if (which == "head_box")          head_box();
    else if (which == "head_camera")       head_camera();
    else if (which == "head_laser")        head_laser();
    else if (which == "vibration")         translate([14,-14,PLATFORM_Z + PLATFORM_T]) vibration_motor();
}
FIXED = ["base", "base_legs", "pan_motor", "pan_motor_screws", "pan_post", "pan_strip", "pan_sensor"];
DECK  = ["platform", "platform_glue", "pan_magnet_n", "pan_magnet_s", "stilts", "bracket",
         "tilt_motor", "tilt_motor_screws"];
TILT  = ["tilt_disc", "tilt_glue", "head_box", "head_camera", "head_laser"];

// ---- the rig, split by what moves ------------------------------------
// Three groups move relative to each other, so tools/cad/check_clearance.sh
// intersects all three pairs. The sensor arm is FIXED: a sensor that
// turns with the magnet it measures reads a constant.
module rig(pan = PAN_DEG, tilt = TILT_DEG) { rig_fixed(); rig_pan_deck(pan); rig_tilt_group(pan, tilt); }
module rig_fixed() { for (p = FIXED) piece(p); }
module rig_pan_deck(pan = PAN_DEG) { rotate([0,0,pan]) for (p = DECK) piece(p); }
module rig_tilt_group(pan = PAN_DEG, tilt = TILT_DEG) {
    rotate([0,0,pan]) translate([0, TILT_Y, TILT_Z]) rotate([tilt,0,0]) translate([0, -TILT_Y, -TILT_Z])
        for (p = TILT) piece(p);
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
    color(C_DESK) translate([-290,-120,-PLATE_T-LEG_H-34]) cube([540, 320, 34]);
}

// ---- views ----------------------------------------------------------
module view_all()  { desk(); rig(); bench_electronics(); scene_targets(); }
module view_rig()  { rig(); }
module view_head() { for (p = ["head_box", "head_camera", "head_laser", "tilt_disc", "tilt_glue"]) piece(p); }
// Exploded, in build order, bottom to top -- the order of the picture
// guide's cards 3 to 7. Labelled, because an exploded view without
// names is half a diagram.
module label(txt, sz = 7) {
    color("#1b1f24") rotate([72,0,30])
        linear_extrude(0.6) text(txt, size = sz, font = "DejaVu Sans:style=Bold");
}
module view_explode() {
    E = [["base_legs", -40, "legs >= 6 cm"], ["pan_motor", -70, "pan motor, 4 x M3x16 + 2 spacer nuts each"],
         ["pan_motor_screws", -30, ""], ["base", 0, "base 15 x 15 cm, 8 mm LOOSE middle hole"],
         ["platform_glue", 30, "M-Seal ring UNDER the disc"], ["platform", 40, "big disc 9 cm, glued on the shaft"],
         ["pan_magnet_n", 60, "diametric magnet on the shaft TIP"], ["pan_magnet_s", 60, ""],
         ["pan_sensor", 80, "AS5600, chip down, 1.5 mm gap"], ["pan_strip", 80, "strip 1.5 x 6 cm"], ["pan_post", 80, "M3x40 post (fixed)"],
         ["stilts", 110, "3 x M3x40 stilts"], ["bracket", 130, "L-bracket on the stilts"],
         ["tilt_motor", 150, "tilt motor, 4 x M3x6"], ["tilt_motor_screws", 150, ""],
         ["tilt_glue", 170, "M-Seal ring"], ["tilt_disc", 170, "small disc 4 cm"],
         ["head_box", 200, "head, flat + centred on the small disc"], ["head_camera", 200, ""], ["head_laser", 200, ""]];
    for (e = E) translate([0, 0, e[1]]) { piece(e[0]); if (e[2] != "") translate([110, 0, 20]) label(e[2]); }
}

// ---- per-part export, for the interactive assembly page -------------
// docs/assembly.html animates the build one component at a time, which
// a single fused mesh cannot do. Each piece is emitted in its FINAL
// assembled position at zero pan and zero tilt, so the page only
// animates an offset back to zero -- no transform chain is re-derived
// in JavaScript, which is exactly where the tilt-axis bug came from
// the first time.
//
//   xvfb-run -a openscad -D 'part="head_box"' -D 'LOWPOLY=true' -o head_box.stl zerodrift_full_assembly.scad
module view_part(which) {
    // the two target units, for the beacon/decoy tab of assembly.html
    if      (which == "beacon_case")   abs_box(90, 60, 40);
    else if (which == "beacon_led")    translate([45, 30, 40]) { led_10mm("#e03131"); translate([0,0,14]) pingpong_ball(); }
    else if (which == "beacon_nano")   translate([16, 12, 40]) arduino_nano_usbc();
    else if (which == "beacon_switch") translate([74, 14, 40]) toggle_switch();
    else if (which == "decoy_case")    abs_box(70, 55, 26);
    else if (which == "decoy_led")     translate([35, 27, 26]) led_10mm("#f1f3f5");
    else if (which == "decoy_cells")   translate([6, 4, -16]) aa_holder_3();
    else if (which == "decoy_switch")  translate([58, 12, 26]) toggle_switch();
    else piece(which);
}

view = "all";
part = "";
if      (part != "")        view_part(part);
else if (view == "all")     view_all();
else if (view == "rig")     view_rig();
else if (view == "head")    view_head();
else if (view == "explode") view_explode();
