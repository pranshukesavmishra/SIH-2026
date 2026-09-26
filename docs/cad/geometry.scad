// ZeroDrift MK2 — the numbers the mechanism imposes
// ================================================
// Shared with `include <>` (not `use <>`, which imports modules but
// NOT variables) by zerodrift_full_assembly.scad and animate.scad, so
// the still renders and the animation cannot drift apart.
//
// This is the build in docs/submission/picture_guide_source.html: the
// parts on hand, NO coupler. Both discs are glued straight onto their
// motor shafts with a ring of M-Seal under the disc, 2 mm of shaft tip
// left clean on top, and the diametric magnet superglued onto that tip.
// The L-bracket stands on three M3 x 40 "stilts" pushed up through the
// big disc; the head box is screwed flat and centred on the small disc.
//
// None of these are styling numbers.

// Shared palette, so both files name the same brass the same way.
C_ACRYLIC = "#cfe3ee";  C_WIRE  = "#2f3336";  C_DESK = "#e9e6e0";
C_BRASS   = "#b08d57";  C_STEEL = "#5b6b7c";

// ---- cut list (picture guide card 1) -------------------------------
PLATE       = 152.4;       // A  base, 15 x 15 cm acrylic square
PLATE_T     = 3;
PLATFORM_D  = 90;          // B  big disc, 9 cm circle
PLATFORM_T  = 3;
TILT_DISC_D = 40;          // C  small disc, 4 cm circle
TILT_DISC_T = 3;
STRIP_L     = 60;          // D  sensor strip, 1.5 x 6 cm
STRIP_W     = 15;
STRIP_T     = 3;
BASE_HOLE_D = 8;           // base middle hole: LOOSE, the shaft must not touch

// ---- base, legs and the pan motor (card 3) ------------------------
LEG_H       = 60;          // legs taller than the motor, so it hangs free
LEG_W       = 20;          // wood blocks
SPACER      = 2 * 2.4;     // two M3 nuts on each motor screw
PAN_FACE_Z  = -PLATE_T - SPACER;       // pan motor face, -7.8
SHAFT_L     = 24;          // NEMA17 shaft, face to tip
TIP_OUT     = 2;           // shaft tip left clean above each disc

// ---- the big disc on the pan shaft (card 4) ------------------------
PAN_TIP_Z   = PAN_FACE_Z + SHAFT_L;                 // 16.2
PLATFORM_Z  = PAN_TIP_Z - TIP_OUT - PLATFORM_T;     // 11.2, disc underside
GLUE_D      = 16;          // M-Seal ring under the disc, round the shaft
GLUE_H      = 6;

// ---- magnet + pan sensor arm (card 5) ------------------------------
// The AS5600 reads the DIRECTION of the field through its die, so it
// must be concentric with the axis and inside a narrow axial band.
// Off-axis it returns a number that is not an angle, and does so
// silently.
MAGNET_D    = 6;
MAGNET_H    = 2.5;
AIRGAP      = 1.5;         // chip face to magnet face; spec band 0.5-3
CHIP_H      = 2.5;         // as5600() board+chip stack, origin at board face
PAN_MAG_TOP = PAN_TIP_Z + MAGNET_H;                 // 18.7
PAN_SENS_Z  = PAN_MAG_TOP + AIRGAP + CHIP_H;        // 22.7, strip underside
PAN_POST_R  = 50;          // "4-5 cm off-centre": just outside the 9 cm disc
POST_L      = 40;          // M3 x 40

// ---- stilts, bracket and the tilt motor (card 6) -------------------
// Three M3 x 40 pushed UP through the big disc, on the side AWAY from
// the sensor arm (the arm is at +X, so the stilts are at -X). The
// bracket's foot sits on their tops, a nut above and below it.
STILT_L     = 40;
STILT_R     = 36;
STILT_ANG   = [150, 180, 210];
NUT_H       = 2.4;
FOOT_T      = 3;
FOOT_Z      = PLATFORM_Z + STILT_L - NUT_H - FOOT_T;  // 45.8, foot underside
FOOT_X0     = -50;         // foot runs from here to the standing leg
LEG_X       = -8;          // tilt motor face = inner face of the standing leg
BRACKET_T   = 3;
BRACKET_W   = 42;
NEMA_HALF   = 42.3 / 2;
TILT_Z      = FOOT_Z + FOOT_T + NUT_H + 1 + NEMA_HALF;  // ~73.5, tilt axis
TILT_Y      = 0;           // tilt axis passes over the pan axis

// ---- small disc + head (card 7) -------------------------------------
TILT_TIP_X  = LEG_X + SHAFT_L;                      // 16
TILT_DISC_X = TILT_TIP_X - TIP_OUT - TILT_DISC_T;   // 11, disc inner face
HEAD_W = 56; HEAD_D = 46; HEAD_H = 42;              // x (along the axis), y, z
HEAD_X      = TILT_DISC_X + TILT_DISC_T + HEAD_W/2; // box centre, flat on the disc
CAM_LASER   = 20;          // camera and laser 2 cm apart, same direction

// Travel. Firmware soft limits (tools/rig/rig_firmware_v2.ino):
// PAN_LIMIT_DEG = 90, TILT_LIMIT_DEG = 18. Past about 150 deg of pan a
// stilt reaches the fixed sensor strip, so +-90 leaves a wide margin.
PAN_LIMIT   = 90;
TILT_MAX    = 18;
TILT_MIN    = -18;

assert(AIRGAP >= 0.5 && AIRGAP <= 3.0,
       "AS5600 air gap is outside the 0.5-3 mm the part needs");
assert(PAN_POST_R - 2.5 > PLATFORM_D / 2,
       "pan sensor post fouls the rotating big disc");
assert(PLATFORM_Z - GLUE_H > 0,
       "M-Seal ring would glue the disc to the base plate");
assert(FOOT_Z > PAN_SENS_Z + STRIP_T + 10,
       "bracket foot does not clear the sensor arm");
assert(TILT_DISC_X - GLUE_H - 2 > LEG_X + BRACKET_T,
       "M-Seal ring would glue the small disc to the bracket");
