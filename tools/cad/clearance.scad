// Clearance probe for zerodrift_full_assembly.scad.
//
// Intersects two kinematic groups of the rig and exports the overlap.
// An empty result means no interference; a solid means two parts want
// the same space at that pose. Driven by check_clearance.sh.
//
// It tests the SHIPPED modules, not a copy, so it cannot drift away
// from the model it guards.
//
// THREE groups move relative to each other, so all three pairs matter:
//   fixed      base plate, pan motor, pan encoder arm
//   deck       platform, riser, tilt bracket, tilt motor, tilt encoder
//   tilt       tilt magnet, standoff, head
// The first version of this test only did fixed-vs-everything-else,
// and missed the head clipping the pan platform at +21 deg of tilt --
// both are carried by the pan shaft, so that pair never got compared.
use <../../docs/cad/zerodrift_full_assembly.scad>

// Coarse facets on purpose: whether two solids share space is decided
// by the bracket, post and motor envelopes, not by how round a
// cylinder is. At full detail one pose took four minutes. LOWPOLY also
// swaps the hulled boxes in parts_lib for plain cubes, which are
// slightly LARGER, so the test errs toward reporting interference
// rather than missing it.
//
// NOTE: -D only overrides a variable the file ALSO assigns. Declaring
// these with is_undef() instead silently pins them to their defaults.
$fn = 12;
LOWPOLY = true;
PANA  = 0;        // pan angle under test, deg
TILTA = 0;        // tilt angle under test, deg
PAIR  = "fd";     // fd = fixed/deck, ft = fixed/tilt, dt = deck/tilt

if      (PAIR == "fd") intersection() { rig_fixed();          rig_pan_deck(PANA); }
else if (PAIR == "ft") intersection() { rig_fixed();          rig_tilt_group(PANA, TILTA); }
else if (PAIR == "dt") intersection() { rig_pan_deck(PANA);   rig_tilt_group(PANA, TILTA); }
