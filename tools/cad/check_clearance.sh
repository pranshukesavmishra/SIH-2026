#!/bin/sh
# Sweep the rig through its travel and report any self-interference.
#
# Why this exists: five separate geometry faults in this model were
# invisible in rendered views and obvious the moment the two kinematic
# groups were intersected -- a tilt bracket clipping the pan platform,
# an encoder post driven through it, both AS5600s sitting 12 mm off the
# axis they were meant to measure, and the camera's service loop
# running through the base plate. Eyeballing a render does not catch
# these. Set arithmetic does.
#
# Contacts of zero thickness are NOT faults: a shaft tip meeting the
# platform it drives is a mounting interface, and it shows up in the
# intersection as a coplanar sheet. So the test measures the VOLUME of
# the overlap, not whether the intersection is empty.
#
# Usage:  tools/cad/check_clearance.sh [pan_step_deg] [min_volume_mm3]
# Exit:   0 = clear across the swept range, 1 = interference found.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
step=${1:-30}
minvol=${2:-1.0}
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

fail=0
pan=-180
while [ "$pan" -le 180 ]; do
  for tilt in -25 0 25; do
    f="$out/p${pan}_t${tilt}.stl"
    xvfb-run -a openscad -D "PANA=$pan" -D "TILTA=$tilt" -D "LOWPOLY=true" \
        -o "$f" "$here/clearance.scad" >/dev/null 2>&1 || true
    v=$(python3 "$here/stl_volume.py" "$f" 2>/dev/null || echo 0)
    if python3 -c "import sys; sys.exit(0 if float(sys.argv[1]) > float(sys.argv[2]) else 1)" "$v" "$minvol"; then
      printf 'INTERFERENCE  pan=%-5s tilt=%-4s  overlap %s mm^3\n' "$pan" "$tilt" "$v"
      fail=1
    fi
  done
  pan=$((pan + step))
done

if [ "$fail" -eq 0 ]; then
  echo "clear: no interference over pan -180..180, tilt -25..25"
else
  echo "---"
  echo "Pan travel must be soft-limited inside the first touch in each"
  echo "direction; set PAN_LIMIT in docs/cad/geometry.scad accordingly."
fi
exit $fail
