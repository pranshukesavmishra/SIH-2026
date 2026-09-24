// ZeroDrift Mk3 — the numbers the mechanism imposes
// ================================================
// Shared with `include <>` (not `use <>`, which imports modules but
// NOT variables) by zerodrift_full_assembly.scad and animate.scad, so
// the still renders and the animation cannot drift apart. They did
// drift once: the animation kept an encoder layout the static model
// had already had corrected, and nothing caught it because both files
// rendered perfectly well.
//
// None of these are styling numbers.

// Shared palette, so both files name the same brass the same way.
C_ACRYLIC = "#cfe3ee";  C_WIRE  = "#2f3336";  C_DESK = "#e9e6e0";
C_BRASS   = "#b08d57";  C_STEEL = "#5b6b7c";

PLATE       = 152.4;       // 6 inch acrylic, as bought
PLATE_T     = 3;

PLATFORM_Z  = 23;          // underside of the pan platform
PLATFORM_T  = 3;
PLATFORM_D  = 60;          // big enough to actually bolt the tilt bracket to
                           // (cut from the second sheet in the pack of 2)

// AS5600 geometry. The chip reads the DIRECTION of the field through
// the die, so it must be concentric with the rotation axis and inside
// a narrow axial band. Off-axis it returns a number that is not an
// angle, and it does so silently.
MAGNET_H    = 2.5;
AIRGAP      = 1.5;         // chip face to magnet face; spec band is 0.5-3
CHIP_H      = 2.5;         // as5600() board+chip stack, origin at board face

PAN_MAG_TOP = PLATFORM_Z + PLATFORM_T + MAGNET_H;      // 28.5
PAN_SENS_Z  = PAN_MAG_TOP + AIRGAP + CHIP_H;           // 32.5
PAN_POST_R  = 38;          // clear of the platform, inside the 152 mm plate

// Height of the tilt axis. NOT a free choice: the head hangs 65 mm
// out from this axis, so tilting down swings it toward the base
// plate. At the 48 mm a plain L-bracket gives, the head hits the
// plate at about +17 deg -- the clearance sweep found it at +25 at
// every pan angle at once, which is what a range limit looks like.
// A 14 mm standoff riser under the bracket (M3 parts already on the
// BOM) buys the full +-25 deg and, as a side effect, lifts the whole
// tilt stage clear of the pan encoder post.
RISER_H      = 14;
TILT_Z       = PLATFORM_Z + PLATFORM_T + RISER_H + 22;   // 62
TILT_DISC_X  = -18;        // tilt shaft end
TILT_DISC_T  = 3;
TILT_MAG_FACE = TILT_DISC_X + TILT_DISC_T + MAGNET_H;  // -12.5
TILT_ARM_X   = -20;        // tilt encoder arm frame origin
// inside rotate([0,90,0]) at TILT_ARM_X, world x = local z + TILT_ARM_X
TILT_SENS_L  = (TILT_MAG_FACE + AIRGAP - TILT_ARM_X) + CHIP_H;   // 11.5

// Travel limits. Both measured by tools/cad/check_clearance.sh and
// then rounded inward, never estimated.
//
// Pan is bounded by the fixed encoder post: past the limit the tilt
// bracket swings into it. First contact at -150 deg; 120 is the
// largest angle actually swept clear.
PAN_LIMIT   = 120;

// Tilt is ASYMMETRIC, and the reason is worth knowing before anyone
// "fixes" it. Tilting toward the plate, the head reaches the PAN
// PLATFORM at +21 deg -- not the base plate, which it only reaches at
// +30. Enlarging the platform to 60 mm (so the tilt bracket had
// something to bolt to) is what created that limit. Tilting away, the
// head is clear past -45.
//
// Positive tilt = head swinging down toward the plate.
TILT_MAX    =  20;
TILT_MIN    = -40;

assert(TILT_MAX < 21, "tilt travel reaches the pan platform at +21 deg");

assert(AIRGAP >= 0.5 && AIRGAP <= 3.0,
       "AS5600 air gap is outside the 0.5-3 mm the part needs");
assert(PAN_POST_R - 2.5 > PLATFORM_D / 2,
       "pan encoder post fouls the rotating platform");
