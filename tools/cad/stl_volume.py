#!/usr/bin/env python3
"""Signed volume of an ASCII STL, in mm^3.

A closed mesh's volume is the sum of the signed volumes of the
tetrahedra formed by each triangle with the origin. For the clearance
test this separates a real interference (a solid, positive volume)
from a mounting interface (two faces touching, volume ~0).
"""
import sys

def volume(path):
    verts, vol = [], 0.0
    try:
        fh = open(path)
    except OSError:
        return 0.0
    with fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("vertex"):
                continue
            verts.append(tuple(float(x) for x in line.split()[1:4]))
            if len(verts) == 3:
                (ax, ay, az), (bx, by, bz), (cx, cy, cz) = verts
                vol += (ax * (by * cz - bz * cy)
                        - ay * (bx * cz - bz * cx)
                        + az * (bx * cy - by * cx)) / 6.0
                verts = []
    return abs(vol)

if __name__ == "__main__":
    print(f"{volume(sys.argv[1]):.3f}")
