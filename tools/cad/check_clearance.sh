#!/bin/sh
# Sweep the rig through its travel and report any self-interference.
#
# Why this exists: ten geometry faults in this model were invisible in
# rendered views and obvious the moment two kinematic groups were
# intersected -- a tilt bracket clipping the pan platform, an encoder
# post driven through it, both AS5600s sitting 12 mm off the axis they
# were meant to measure, the camera service loop running through the
# base plate, and the head reaching both the base plate and the
# platform at the top of its tilt travel. Eyeballing a render does not
# catch these. Set arithmetic does.
#
# Three groups move relative to each other, so all three pairs are
# tested. An earlier version compared only the frame against
# everything else and missed the head-vs-platform contact, because
# both of those ride the pan shaft.
#
# Mounting interfaces are NOT faults. Two kinds show up in the
# intersection and neither is a defect:
#   - a shaft tip meeting the platform it drives, as a coplanar sheet
#     of zero thickness;
#   - a shaft seated INSIDE its hub, as a real solid -- the tilt magnet
#     disc sits on the tilt motor shaft, which is a constant ~136 mm^3
#     of honest overlap at every pose.
# So this measures the VOLUME of the overlap and compares it against
# the same pair's volume at the neutral pose. A mounting interface is
# pose-independent; a clash appears as GROWTH above that baseline.
#
# Usage:  tools/cad/check_clearance.sh [pan_step_deg] [min_volume_mm3]
# Exit:   0 = clear across the swept range, 1 = interference found.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
step=${1:-30}
minvol=${2:-1.0}
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

probe() {   # pair pan tilt -> overlap volume in mm^3
  # A unique file per probe. Sharing one output path silently
  # re-measures the PREVIOUS pose whenever a render comes back empty,
  # since OpenSCAD writes no file in that case.
  f="$out/p$2_t$3_$1.stl"
  xvfb-run -a openscad -D "PANA=$2" -D "TILTA=$3" -D "PAIR=\"$1\"" \
      -D "LOWPOLY=true" -o "$f" "$here/clearance.scad" >/dev/null 2>&1 || true
  python3 "$here/stl_volume.py" "$f" 2>/dev/null || echo 0
}

# Baseline: the mounting overlap each pair carries at the neutral pose.
for pair in fd ft dt; do
  eval "base_$pair=$(probe $pair 0 0)"
done
echo "baseline overlap at the neutral pose (mounting interfaces):"
echo "  fixed/deck=$base_fd  fixed/tilt=$base_ft  deck/tilt=$base_dt"

fail=0
pan=-180
while [ "$pan" -le 180 ]; do
  for tilt in -25 0 20 25; do
    for pair in fd ft dt; do
      v=$(probe "$pair" "$pan" "$tilt")
      eval "b=\$base_$pair"
      if python3 -c "import sys; sys.exit(0 if float(sys.argv[1]) - float(sys.argv[2]) > float(sys.argv[3]) else 1)" "$v" "$b" "$minvol"; then
        printf 'INTERFERENCE  pan=%-5s tilt=%-4s %s  overlap %s mm^3 (baseline %s)\n' \
               "$pan" "$tilt" "$pair" "$v" "$b"
        fail=1
      fi
    done
  done
  pan=$((pan + step))
done

if [ "$fail" -eq 0 ]; then
  echo "clear: no interference over pan -180..180, tilt -25..25"
else
  echo "---"
  echo "Soft-limit travel inside the first touch in each direction and"
  echo "set PAN_LIMIT / TILT_LIMIT in docs/cad/geometry.scad to match."
fi
exit $fail
