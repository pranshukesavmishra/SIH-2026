#!/usr/bin/env python3
"""Convert OpenSCAD's ASCII STL output to binary STL.

OpenSCAD only writes ASCII, which is roughly five times the size of the
same mesh in binary. That does not matter for a file you open in a
viewer; it matters a great deal for docs/assembly.html, which fetches
twelve of them over the network before it can draw anything.

Usage: stl_to_binary.py <in.stl> <out.stl>
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def read_ascii(path: Path):
    """Yield (normal, (v0, v1, v2)) per facet."""
    normal, verts = (0.0, 0.0, 0.0), []
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "facet" and len(parts) >= 5:
            normal = tuple(float(x) for x in parts[2:5])
            verts = []
        elif parts[0] == "vertex":
            verts.append(tuple(float(x) for x in parts[1:4]))
            if len(verts) == 3:
                yield normal, verts
                verts = []


def main() -> int:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    facets = list(read_ascii(src))
    with dst.open("wb") as fh:
        fh.write(b"ZeroDrift Mk3 - generated, do not edit".ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(facets)))
        for n, (a, b, c) in facets:
            fh.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    print(f"{src.name}: {len(facets)} facets, "
          f"{src.stat().st_size:,} -> {dst.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
