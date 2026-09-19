// ZeroDrift Mk3 — part library
// =============================
// One module per physical item on docs/data/bom_tier_a.json, drawn to
// its real catalogue dimensions. Convention throughout: a part's
// MOUNTING FACE sits in the XY plane at the origin and whatever it
// drives or presents extends +Z, so placing one is a translate plus at
// most one rotate.

$fn = 72;

// ---- palette -------------------------------------------------------
C_MOTOR   = "#3a3d42";  C_SHAFT  = "#c9ccd1";  C_BRACKET = "#5b6b7c";
C_ACRYLIC = "#cfe3ee";  C_PCB_R  = "#a8342a";  C_PCB_B   = "#1d5a8a";
C_PCB_G   = "#1f7a4d";  C_BOARD  = "#e8e4d9";  C_MAGNET  = "#c0392b";
C_HEATSNK = "#8d9298";  C_ABS    = "#d9822b";  C_BATT    = "#7d5fb2";
C_BRASS   = "#b08d57";  C_BLACK  = "#23262a";  C_WIRE    = "#2f3336";
C_LED_R   = "#e03131";  C_LED_W  = "#f1f3f5";  C_FILTER  = "#cc2936";

module rbox(sz, r = 1.2) {          // rounded box, for parts that have one
    hull() for (x = [r, sz[0]-r], y = [r, sz[1]-r], z = [r, sz[2]-r])
        translate([x,y,z]) sphere(r = r);
}

// ---- A. Motion -----------------------------------------------------
NEMA_FACE = 42.3; NEMA_LEN = 40; NEMA_BC = 31; NEMA_BOLT = 3.2;
NEMA_BOSS_D = 22; NEMA_BOSS_H = 2; NEMA_SHAFT_D = 5; NEMA_SHAFT_L = 22;

module nema17(shaft_len = NEMA_SHAFT_L) {
    color(C_MOTOR) {
        // body with the chamfered corners a real NEMA17 has
        translate([0,0,-NEMA_LEN])
            intersection() {
                translate([-NEMA_FACE/2,-NEMA_FACE/2,0])
                    cube([NEMA_FACE, NEMA_FACE, NEMA_LEN]);
                cylinder(d = NEMA_FACE*1.29, h = NEMA_LEN, $fn = 4+60);
            }
        // end bells, slightly proud, as on the real casting
        for (z = [-NEMA_LEN, -6])
            translate([0,0,z]) linear_extrude(6)
                offset(r = 0.6) square(NEMA_FACE - 1.2, center = true);
        translate([0,0,-NEMA_BOSS_H]) cylinder(d = NEMA_BOSS_D, h = NEMA_BOSS_H);
    }
    color(C_SHAFT) cylinder(d = NEMA_SHAFT_D, h = shaft_len);
    color(C_BLACK) for (a = [45,135,225,315])
        translate([NEMA_BC/2*cos(a), NEMA_BC/2*sin(a), -5])
            cylinder(d = NEMA_BOLT, h = 6);
    // 4-wire lead leaving the back
    color(C_WIRE) translate([0,-NEMA_FACE/2+4,-NEMA_LEN+8])
        rotate([90,0,0]) cylinder(d = 3.4, h = 10);
}

module a4988() {                     // 20 x 15 PCB + heatsink
    color(C_PCB_R) translate([-10,-7.5,0]) cube([20,15,1.6]);
    color(C_HEATSNK) translate([-5,-5,1.6])            // 9x9x5 heatsink
        for (i = [0:3]) translate([i*2.6,0,0]) cube([1.4,10,5]);
    color(C_BLACK) translate([-2.5,-2.5,1.6]) cube([5,5,1]);   // driver IC
    color("#d4c05a") translate([7,0,1.6]) cylinder(d = 3.4, h = 2.2);  // Vref pot
    color(C_BLACK) for (s = [-1,1], i = [0:7])       // pin headers
        translate([s*9, -7 + i*2, -3]) cylinder(d = 0.7, h = 3);
}

module l_bracket(leg = 34, th = 3, w = NEMA_FACE) {
    color(C_BRACKET) {
        cube([w, leg, th]);
        translate([0, leg - th, 0]) cube([w, th, leg]);
        // gusset, as on a real stamped bracket
        translate([0, leg-th, 0]) rotate([0,-90,0])
            linear_extrude(2, center = false)
            polygon([[0,0],[leg*0.6,0],[0,-leg*0.6]]);
    }
}

module cap100uf() {                  // 100 uF 25 V electrolytic, 8 x 12
    color("#2b4a7a") cylinder(d = 8, h = 12);
    color("#9aa3ad") translate([0,0,12]) cylinder(d = 8, h = 0.6);
    color(C_WIRE) for (s = [-1,1]) translate([s*1.8,0,-4]) cylinder(d = 0.6, h = 4);
}

// ---- B. Feedback ---------------------------------------------------
module as5600() {                    // ~11 x 11 breakout
    color(C_PCB_B) translate([-5.5,-5.5,0]) cube([11,11,1.6]);
    color(C_BLACK) translate([-2,-2,1.6]) cube([4,4,0.9]);
    color("#d4c05a") for (i = [0:5]) translate([-5.5+1.3+i*1.7, -6.8, 0.8])
        cube([0.7,2.5,0.7]);
}
module diametric_magnet() {          // 6 x 2.5, poles across the diameter
    color(C_MAGNET) cylinder(d = 6, h = 2.5);
    color("#7d1f18") translate([-3,-0.25,0]) cube([6,0.5,2.51]);  // pole line
}
module tca9548a() {                  // ~20 x 15 breakout
    color(C_PCB_B) translate([-10,-7.5,0]) cube([20,15,1.6]);
    color(C_BLACK) translate([-3,-2.5,1.6]) cube([6,5,1]);
    color("#d4c05a") for (i = [0:7]) translate([-9+i*2.3, -8.6, 0.8]) cube([0.7,2.5,0.7]);
}

// ---- C. Head -------------------------------------------------------
module webcam_board() {              // de-housed UVC webcam PCB + lens
    color(C_PCB_G) translate([-16,-16,0]) cube([32,32,1.6]);
    color(C_BLACK) translate([0,0,1.6]) cylinder(d = 12, h = 9);    // lens barrel
    color("#11151a") translate([0,0,10.6]) cylinder(d = 9.5, h = 0.8);
    color(C_WIRE) translate([-16,0,3]) rotate([0,-90,0]) cylinder(d = 3.6, h = 6);
}
module red_filter(w = 18) {          // gel / acrylic offcut over the lens
    color(C_FILTER, 0.45) translate([-w/2,-w/2,0]) cube([w,w,1.2]);
}
module ky008_laser() {               // brass barrel module, as photographed
    color(C_BRASS) cylinder(d = 6.5, h = 18);
    color(C_BLACK) translate([0,0,-4]) cube([8,8,4], center = false);
    color(C_WIRE) for (s = [-1,1]) translate([s*2, 2, -8]) cylinder(d = 0.8, h = 5);
}
// Deliberately see-through: this is a documentation model, and an
// opaque box is a box with the interesting part hidden inside it.
// Real enclosures are opaque; what matters here is what goes in them
// and where it points.
module abs_box(w, d, h, lid = true, alpha = 0.18) {
    color(C_ABS, alpha) difference() {
        rbox([w,d,h], 2);
        translate([2,2,2]) cube([w-4, d-4, h]);
    }
    if (lid) color(C_ABS, alpha*0.6) translate([0,0,h]) rbox([w,d,2], 1);
    // edge lines so the box still reads as a solid object when clear
    color(C_ABS, 0.85) for (x = [0,w], y = [0,d])
        translate([x,y,0]) cylinder(d = 1.1, h = h, $fn = 10);
}

// ---- D. Control and power ------------------------------------------
module breadboard() {                // 830 point, 165 x 55 x 10
    color(C_BOARD) rbox([165, 55, 10], 1.5);
    color("#c9302c") translate([4, 51, 10]) cube([157, 0.7, 0.1]);
    color("#2f6fb5") translate([4, 3.5, 10]) cube([157, 0.7, 0.1]);
    color("#b9b4a6") translate([4, 27, 10]) cube([157, 1.6, 0.2]);   // centre trench
}
module arduino_nano_usbc() {         // 45 x 18, USB-C (the new revision)
    color(C_PCB_B) translate([-22.5,-9,0]) cube([45,18,1.6]);
    color("#9aa3ad") translate([-22.5,-4.4,1.6]) cube([7.5,8.8,3.2]);  // USB-C
    color(C_BLACK) translate([-6,-5,1.6]) cube([12,10,1.2]);           // MCU
    color("#d4c05a") for (s = [-1,1], i = [0:14])
        translate([-21 + i*3, s*8.2, 0.6]) cube([0.7,0.7,0.7]);
}
module pack_18650_3s() {             // 3 x 18650 in a holder, ~75 x 58 x 20
    color(C_BLACK) rbox([75, 58, 6], 1);
    for (i = [0:2]) color(C_BATT)
        translate([5, 6 + i*17, 6]) rotate([0,90,0]) cylinder(d = 18, h = 65);
    color(C_WIRE) translate([75,29,10]) rotate([0,90,0]) cylinder(d = 3, h = 30);
}
module barrel_to_screw() {
    color(C_BLACK) rbox([22, 14, 11], 1);
    color("#9aa3ad") translate([0,7,5.5]) rotate([90,0,0]) cylinder(d = 8, h = 6);
    color("#d4c05a") for (s = [-1,1]) translate([11 + s*4, 7, 11]) cylinder(d = 3, h = 1.2);
}
module toggle_switch() {             // SPST, 6mm bushing
    color(C_BLACK) translate([-7.5,-6,-12]) cube([15,12,12]);
    color("#9aa3ad") cylinder(d = 6, h = 4);
    color("#c9302c") translate([0,0,4]) cylinder(d = 3, h = 9);
    color("#c9302c") translate([0,0,13]) sphere(d = 4.5);
    color(C_WIRE) for (i = [-1,0,1]) translate([i*4, 0, -16]) cylinder(d = 1, h = 4);
}

// ---- E. Disturbance injector ---------------------------------------
module vibration_motor() {           // 3 V coin type, 10 mm
    color("#b8bcc2") cylinder(d = 10, h = 3.4);
    color(C_WIRE) for (s = [-1,1]) translate([s*2, 0, -6]) cylinder(d = 0.9, h = 6);
}

// ---- F/G. Beacon and decoy -----------------------------------------
module led_10mm(col = C_LED_R) {
    color(col, 0.85) { cylinder(d = 10, h = 7); translate([0,0,7]) sphere(d = 10); }
    color("#9aa3ad") translate([0,0,-1]) cylinder(d = 11, h = 1.2);
    color(C_WIRE) for (s = [-1,1]) translate([s*2.5,0,-16]) cylinder(d = 0.8, h = 15);
}
module pingpong_ball() { color("#f5f3ef", 0.4) sphere(d = 40); }
module aa_holder_3() {               // 3 x AA, ~58 x 48 x 15
    color(C_BLACK) rbox([58, 48, 15], 1.2);
    for (i = [0:2]) color("#2d6a4f")
        translate([4, 8 + i*14, 15]) rotate([0,90,0]) cylinder(d = 14, h = 50);
    color(C_WIRE) translate([58,24,8]) rotate([0,90,0]) cylinder(d = 2.4, h = 25);
}

// ---- consumables ---------------------------------------------------
module wire_run(pts, d = 2.2, col = C_WIRE) {
    color(col) for (i = [0:len(pts)-2]) hull() {
        translate(pts[i]) sphere(d = d);
        translate(pts[i+1]) sphere(d = d);
    }
}
module m3_standoff(len) {
    color(C_BRASS) { cylinder(d = 6, h = len, $fn = 6); }
}
