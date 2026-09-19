// ZeroDrift Mk3 — assembly + motion animation
// ===========================================
// One timeline, driven by OpenSCAD's $t (0..1):
//
//   0.00 - 0.45   parts fly in from exploded positions, bottom-up, in
//                 the same order as TERMINAL_MK3.md section 3's stages
//   0.45 - 0.55   settle, whole rig visible
//   0.55 - 1.00   the mechanism runs: pan sweeps, tilt tracks
//
// A slow turntable runs underneath the whole thing so every face is
// seen at least once.
//
//   for i in $(seq -w 0 119); do
//     openscad -D "\$t=$(echo "$i/120" | bc -l)" -o frames/f$i.png animate.scad
//   done
//   ffmpeg -framerate 30 -i frames/f%03d.png -c:v libx264 -pix_fmt yuv420p out.mp4

use <parts_lib.scad>
include <geometry.scad>     // the mechanism's numbers, shared with the still model
$fn = 32;

// ---- timeline helpers ----------------------------------------------
function clamp01(x) = max(0, min(1, x));
// smoothstep, so parts ease into place instead of arriving linearly
function ease(x) = (x*x*(3-2*x));
// a part's arrival: starts at t0, lands at t1, returns 0..1
function arrive(t0, t1) = ease(clamp01(($t - t0) / (t1 - t0)));

// motion phase: pan sweeps, tilt follows, only after assembly is done
PHASE  = clamp01(($t - 0.55) / 0.45);
PAN    = (($t < 0.55) ? 0 : 55 * sin(PHASE * 360));
assert(abs(PAN) <= PAN_LIMIT, "animation pans past the mechanical limit");
TILT   = (($t < 0.55) ? 0 : 18 * sin(PHASE * 360 + 90) - 4);

// ---- the assembly, with each part flown in --------------------------
module rig_animated() {
    // 2 - base plate is the datum; it is simply there
    color("#cfe3ee", 0.45) difference() {
        translate([-PLATE/2,-PLATE/2,-PLATE_T]) cube([PLATE, PLATE, PLATE_T]);
        cylinder(d = 8, h = 20, center = true);
        for (a = [45,135,225,315])
            rotate([0,0,a]) translate([31/2,0,0]) cylinder(d = 3.4, h = 20, center = true);
    }

    // 1 - pan motor rises to meet the plate underside
    translate([0, 0, -PLATE_T - (1 - arrive(0.02, 0.14)) * 90])
        nema17(shaft_len = 26);

    // 4 - the pan encoder arm is FIXED TO THE FRAME, so it is placed
    // outside rotate([0,0,PAN]). It sat inside it until the clearance
    // sweep caught it: a post that turns with the magnet it measures
    // reads a constant, and the animation showed it sweeping round
    // with the platform as if that were the intent.
    translate([(1 - arrive(0.24, 0.33)) * 60, 0, 0]) {
        color(C_BRASS) translate([PAN_POST_R,0,0]) cylinder(d = 5, h = PAN_SENS_Z + 3);
        color("#5b6b7c") translate([-6,-5,PAN_SENS_Z]) cube([PAN_POST_R + 12, 10, 3]);
        translate([0,0,PAN_SENS_Z]) rotate([180,0,0]) as5600();   // chip ON the axis
    }

    rotate([0, 0, PAN]) {
        // 3 - platform + diametric magnet drop onto the shaft
        translate([0, 0, PLATFORM_Z + (1 - arrive(0.14, 0.24)) * 70]) {
            color("#5b6b7c") cylinder(d = PLATFORM_D, h = PLATFORM_T);
            translate([0,0,PLATFORM_T]) diametric_magnet();
        }

        // 5/6/7/8 - tilt stage.
        //
        // Derived, not guessed. The requirement is: tilt axis
        // HORIZONTAL and perpendicular to the look direction, head
        // looking HORIZONTALLY. An earlier version nested
        // rotate([0,TILT,0]) inside rotate([-90,0,0]), which put the
        // tilt axis along world -Z and the look direction along +Z --
        // i.e. a second pan, with the camera staring at the ceiling.
        // Checked numerically before rebuilding.
        //
        //   tilt axis  = world X     (horizontal, across the look)
        //   look       = world -Y    (horizontal, out of the rig)
        //   motor shaft= world X     (rotate([0,90,0]) sends +Z to +X)
        translate([0, 6, TILT_Z + (1 - arrive(0.33, 0.42)) * 80]) {
            // bracket sits ON the platform; motor body extends -X
            translate([-46, -20, PLATFORM_Z + PLATFORM_T - TILT_Z])
                l_bracket(leg = 30, th = 3, w = 30);
            translate([-40, 0, 0]) rotate([0, 90, 0]) nema17(shaft_len = 22);

            // Tilt AS5600 arm: fixed to the motor side of the joint, so
            // outside the rotating group. It reaches UP over the shaft
            // -- reaching down drove the post through the pan platform.
            translate([TILT_ARM_X, 0, 0]) rotate([0, 90, 0]) {
                color(C_BRASS) translate([-26,0,-4]) cylinder(d = 5, h = 22);
                color("#5b6b7c") translate([-28,-4,TILT_SENS_L]) cube([30, 8, 3]);
                translate([0, 0, TILT_SENS_L]) rotate([180,0,0]) as5600();
            }

            // everything from here turns with the tilt axis (world X)
            rotate([TILT, 0, 0]) {
                translate([TILT_DISC_X, 0, 0]) rotate([0,90,0]) {
                    color("#5b6b7c") cylinder(d = 34, h = TILT_DISC_T);
                    translate([0,0,TILT_DISC_T]) diametric_magnet();
                }
                // brass standoff out along -Y, head on its end
                translate([0, (1 - arrive(0.42, 0.52)) * -70, 0]) {
                    color(C_BRASS) rotate([90,0,0]) cylinder(d = 6, h = 42, $fn = 6);
                    translate([0, -65, 0]) head_lite(beam = ($t > 0.60));
                }
            }
        }
        translate([14,-14,PLATFORM_Z + PLATFORM_T]) vibration_motor();
    }
}

// lighter head for animation: same geometry, fewer facets
module head_lite(beam = false) {
    translate([-36,-23,-21]) abs_box(72, 46, 42);
    translate([-16,-14,0]) rotate([90,0,0]) {
        webcam_board();
        translate([0,0,10.6]) red_filter(22);
    }
    // Beam is drawn HERE, inside the laser's own transform, rather than
    // re-deriving the chain outside it -- the first attempt did that and
    // sent the beam straight up instead of down the boresight.
    translate([20,-5,-2]) rotate([90,0,0]) {
        ky008_laser();
        if (beam) color("#ff2d2d", 0.22)
            translate([0,0,18]) cylinder(d1 = 1.6, d2 = 10, h = 320);
    }
}

rotate([0, 0, 20 + $t * 300]) rig_animated();
