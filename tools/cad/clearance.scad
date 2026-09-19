// Clearance probe for zerodrift_full_assembly.scad.
//
// Intersects the two kinematic groups of the rig and exports the
// overlap. An empty result means no interference; any solid means two
// parts occupy the same space at that pose. Driven by check_clearance.sh.
//
// This tests the SHIPPED modules, not a copy of them, so it cannot
// drift away from the model it is meant to guard.
use <../../docs/cad/zerodrift_full_assembly.scad>
$fn = 24;

PANA = 0;       // pan angle under test, deg
TILTA = 0;      // tilt angle under test, deg

intersection() {
    rig_fixed();
    rig_rotating(PANA, TILTA);
}
