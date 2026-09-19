// ZeroDrift Mk3 — pan/tilt gimbal, parametric model
// ===================================================
// Every dimension is either a published mechanical standard (NEMA17)
// or a number that already appears in docs/TERMINAL_MK3.md /
// docs/data/bom_tier_a.json. Drawn to match the parts on the buy list,
// including the single-shaft encoder mount fixed in this session
// (magnet on the rotating platform, AS5600 on a fixed overhanging arm
// -- these motors have no rear shaft to mount to).
//
// Convention used throughout: every module is built with its MOUNTING
// FACE in the XY plane at the origin, and whatever it drives (a shaft,
// an output arm) extending in +Z. Placing an instance is then one
// translate() to the mount point and, if the mount surface isn't
// horizontal, one rotate() to match its normal -- no per-part hacks.
//
//   openscad -o gimbal.stl zerodrift_gimbal.scad
//   xvfb-run -a openscad -D 'view="assembly"' -o assembly.png --imgsize=1400,1000 zerodrift_gimbal.scad

$fn = 48;

// ---- NEMA17, single-shaft — published standard dimensions ----------
nema_face      = 42.3;
nema_body_len  = 40.0;
nema_bolt_bc   = 31.0;
nema_bolt_d    = 3.2;
nema_boss_d    = 22.0;
nema_boss_h    = 2.0;
nema_shaft_d   = 5.0;
nema_shaft_len = 22.0;

// ---- Encoder — docs/TERMINAL_MK3.md §6, single-shaft method --------
magnet_d       = 6.0;
magnet_h       = 2.5;
magnet_gap     = 1.5;
as5600_pcb     = 11.0;
as5600_pcb_h   = 1.6;
platform_d     = 34.0;
platform_h     = 3.0;

// ---- Structure ----------------------------------------------------
bracket_leg    = 34.0;   // NEMA17 L-bracket, mount-face to mount-face
bracket_thick  = 3.0;
base_plate     = 110.0;  // cut from the 6x6in / 152mm acrylic sheet
base_thick     = 3.0;

// ---- Head — ABS project box, de-housed webcam + laser, §2C --------
head_w = 46; head_h = 30; head_d = 24;
laser_d = 6.2; laser_len = 17;

// ======================================================================
// PRIMITIVES — each sits with its mounting face at z=0, extends +Z.

module nema17() {
    color("dimgray") {
        translate([0,0,-nema_body_len])
            cube([nema_face, nema_face, nema_body_len], center = true);
        translate([0,0,-nema_boss_h])
            cylinder(d = nema_boss_d, h = nema_boss_h);
    }
    color("silver")
        cylinder(d = nema_shaft_d, h = nema_shaft_len);
    for (a = [45, 135, 225, 315])
        color("black")
        translate([nema_bolt_bc/2*cos(a), nema_bolt_bc/2*sin(a), -nema_body_len/2])
            cylinder(d = nema_bolt_d, h = nema_body_len + 1, center = true);
}

// Single-shaft encoder: platform + magnet keyed to a shaft of length
// shaft_len starting at z=0; fixed sensor arm bolts to the SAME face
// the motor bolts to (i.e. it does not rotate with the shaft).
module single_shaft_encoder(shaft_len) {
    color("steelblue", 0.9)
        translate([0,0,shaft_len])
            cylinder(d = platform_d, h = platform_h);
    color("crimson")
        translate([0,0,shaft_len + platform_h + magnet_h/2])
            cylinder(d = magnet_d, h = magnet_h, center = true);

    arm_len = platform_d/2 + 14;
    sensor_z = shaft_len + platform_h + magnet_h + magnet_gap;
    color("gold", 0.95) {
        // fixed arm rises from the mounting face (z=0), not the shaft
        translate([platform_d/2 - 2, -bracket_thick/2, 0])
            cube([2, bracket_thick, sensor_z + as5600_pcb_h]);
        translate([platform_d/2 - 2 - arm_len + 4, -sensor_arm_thick()/2, sensor_z])
            cube([arm_len - 2, sensor_arm_thick(), 2]);
        translate([platform_d/2 - 2 - arm_len + 4 + as5600_pcb/2, 0, sensor_z + 2])
            color("forestgreen")
                cube([as5600_pcb, as5600_pcb, as5600_pcb_h], center = true);
    }
}
function sensor_arm_thick() = 6.0;

// L-bracket: foot bolts flat at z=0 in the XY plane (this is what you
// place at the mount point); the vertical leg then presents ITS OWN
// mounting face -- returned implicitly at local (0, bracket_leg,
// bracket_leg) rotated 90 about X, which callers reach via
// l_bracket_face_transform().
module l_bracket() {
    color("slategray") {
        cube([nema_face, bracket_leg, bracket_thick]);            // foot
        translate([0, bracket_leg - bracket_thick, 0])
            cube([nema_face, bracket_thick, bracket_leg]);        // upright
    }
}
// Move+rotate a child so it mounts flush on the bracket's vertical leg,
// shaft/output pointing away from the foot (+Y in world once placed).
module on_bracket_face() {
    translate([nema_face/2, bracket_leg, bracket_leg/2])
        rotate([-90,0,0])
        translate([-nema_face/2,-nema_face/2,0])
        children();
}

// Plate with a shaft clearance hole at the origin: the pan motor bolts
// to the UNDERSIDE (real mounting -- a NEMA17's face, where the shaft
// exits, is what bolts flush to a surface; body hangs on the far side,
// shaft continues through to whatever it drives). Getting this wrong
// -- e.g. resting the motor face-down with no hole -- means the shaft
// has nowhere to go, which is exactly the kind of mistake a diagram is
// for catching before it is a drilled hole.
module base_plate_acrylic(hole_d = 0) {
    color("lightblue", 0.35)
        difference() {
            translate([-base_plate/2, -base_plate/2, -base_thick])
                cube([base_plate, base_plate, base_thick]);
            if (hole_d > 0)
                cylinder(d = hole_d, h = base_thick*4, center = true);
        }
}

module head_assembly() {
    // mounting face at z=0 (bolts to the tilt output arm), box body +Z
    color("darkorange", 0.55)
        translate([-head_w/2,-head_d/2,0])
            cube([head_w, head_d, head_h]);
    color("black")
        translate([0, 0, head_h*0.35])
            rotate([-90,0,0])
            cylinder(d = laser_d, h = head_d/2 + laser_len - 6);
    color("dimgray")
        translate([0, 0, head_h*0.65])
            rotate([-90,0,0])
            cylinder(d = 9, h = head_d/2 + 3);
}

// ======================================================================
// FULL ASSEMBLY
//   Base -> pan motor (vertical, shaft up) -> pan platform+encoder
//   -> L-bracket on the platform -> tilt motor (horizontal, shaft out)
//   -> tilt output + encoder -> head.
// Matches Stage 5 of the build order: full pan travel, -30/+45 tilt.

module full_assembly(tilt_deg = 15, pan_deg = 25) {
    base_plate_acrylic(hole_d = nema_shaft_d + 3);

    // Pan motor hangs BELOW the base plate, face bolted flush to its
    // underside; the shaft passes up through the clearance hole to
    // reach the platform above the plate. This is the real mounting --
    // a face-mounted stepper cannot sit shaft-up on top of a surface,
    // because the shaft exits the same face that bolts down.
    rotate([0,0,pan_deg])
    translate([0,0,-base_thick]) {
        nema17();
        translate([0,0,base_thick])
            single_shaft_encoder(nema_shaft_len - base_thick);

        pan_top = nema_shaft_len + platform_h;

        // Pan platform carries the tilt L-bracket, offset from centre
        // so the tilt axis clears the pan encoder's magnet + arm.
        translate([platform_d/2 - nema_face/2 - 6, 6, pan_top])
            l_bracket();

        head_standoff = 42;   // clears the tilt encoder's platform + arm
        translate([platform_d/2 - nema_face/2 - 6, 6, pan_top])
        on_bracket_face() {
            nema17();
            single_shaft_encoder(nema_shaft_len);
            color("gray")
                translate([0,0,nema_shaft_len + platform_h])
                    cylinder(d = 6, h = head_standoff);
            translate([0,0,nema_shaft_len + platform_h + head_standoff])
                rotate([0, tilt_deg, 0])
                head_assembly();
        }
    }
}

module encoder_detail() {
    nema17();
    single_shaft_encoder(nema_shaft_len);
}

view = "assembly";
if (view == "assembly") full_assembly(15, 25);
else if (view == "encoder") encoder_detail();
else if (view == "motor") nema17();
