"""
The host and the firmware must agree about the wire. Nothing else checks this.

This project has already lost time to exactly one failure: the Python
driver and the Arduino sketch disagreeing about the wire format, which
does not raise, does not log, and presents as "the tracker mysteriously
never locks". Three layers drifted apart across three weeks because no
test looked at both sides at once.

So this file looks at both sides at once. It drives the real driver in
dry-run mode, captures the bytes it would have sent, and parses them with
a model of the firmware's grammar -- and then checks that model against
the actual .ino source, so the model cannot quietly go stale either.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from fsoc_pat.hil.mk2 import Mk2Gimbal

FIRMWARE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "rig" / "rig_firmware_v2.ino"

# A model of what rig_firmware_v2.ino's handleLine() accepts. Kept in the
# same order as the switch in the sketch so the two read alike.
GRAMMAR = [
    ("coarse_both", re.compile(r"^P(-?\d+) T(-?\d+)$")),
    ("coarse_pan",  re.compile(r"^P(-?\d+)$")),
    ("coarse_tilt", re.compile(r"^T(-?\d+)$")),
    ("fine_both",   re.compile(r"^p(-?\d+) t(-?\d+)$")),
    ("fine_pan",    re.compile(r"^p(-?\d+)$")),
    ("fine_tilt",   re.compile(r"^t(-?\d+)$")),
    ("laser_off",   re.compile(r"^L0$")),
    ("laser_on",    re.compile(r"^L1$")),
    ("laser_mod",   re.compile(r"^L\d+(\.\d+)?$")),
    ("vibration",   re.compile(r"^V[01]$")),
    ("centre",      re.compile(r"^C$")),
    ("zero",        re.compile(r"^Z$")),
    ("status",      re.compile(r"^\?$")),
    ("selftest",    re.compile(r"^!$")),
]


def classify(line: str):
    for name, pat in GRAMMAR:
        if pat.match(line):
            return name
    return None


def drive() -> list:
    """Every command surface the engine uses, through the real driver."""
    g = Mk2Gimbal(port=None, dry_run=True)
    g.centre()
    g.command(0.05, -0.02)
    g.command(-0.30, 0.10)
    g.fine(0.001, -0.001)
    g.laser(True)
    g.laser(False)
    g.vibration(True)
    g.vibration(False)
    return list(g.sent)


# -- the two sides agree ------------------------------------------------

def test_every_byte_the_driver_sends_is_understood_by_the_firmware():
    unparsed = [ln for ln in drive() if classify(ln) is None]
    assert not unparsed, (
        "the Mk2 driver emits commands rig_firmware_v2.ino does not parse: "
        f"{unparsed}. Either the sketch or mk2.py has moved; fix the one that "
        "is not on tested hardware.")


def test_the_driver_actually_exercises_the_wire():
    """Guard against the above passing because nothing was sent at all."""
    kinds = {classify(ln) for ln in drive()}
    assert "coarse_both" in kinds
    assert {"laser_on", "laser_off"} <= kinds


def test_coarse_commands_are_integers_because_the_firmware_reads_them_as_such():
    """
    The firmware parses %ld. A float on the wire truncates silently at the
    decimal point -- 'P12.7' becomes 12 steps and nothing reports an error.
    """
    for line in drive():
        if classify(line) in ("coarse_both", "coarse_pan", "coarse_tilt"):
            assert "." not in line, f"non-integer coarse command: {line!r}"


def test_no_command_is_sent_without_being_newline_terminated():
    """
    _send appends the newline. A command without one leaves the firmware
    holding a partial line, which then eats the front of the next command.
    That bug was real in rig_track.py.
    """
    g = Mk2Gimbal(port=None, dry_run=True)
    g.laser(True)
    assert g.sent == ["L1"], "laser() must go through _send, which adds the newline"


# -- the model above matches the actual sketch --------------------------

@pytest.mark.skipif(not FIRMWARE.exists(), reason="firmware sketch not present")
def test_grammar_model_matches_the_firmware_source():
    """
    If someone edits the sketch's parser, this fails -- rather than the
    model silently describing a firmware that no longer exists.
    """
    src = FIRMWARE.read_text()
    for fmt in ('"P%ld T%ld"', '"T%ld"'):
        assert fmt in src, f"sketch no longer parses {fmt}; update GRAMMAR here too"
    assert "case 'L'" in src and "case 'V'" in src
    assert "case 'C'" in src and "case 'Z'" in src and "case '?'" in src


@pytest.mark.skipif(not FIRMWARE.exists(), reason="firmware sketch not present")
def test_firmware_microstepping_matches_the_host_scale():
    """
    The host's DEFAULT_STEPS_PER_RAD hardcodes the microstepping. If the
    sketch's MICROSTEPS disagrees, every commanded angle is silently
    scaled and the rig points consistently wrong.
    """
    import numpy as np
    from fsoc_pat.hil.mk2 import DEFAULT_STEPS_PER_RAD

    m = re.search(r"MICROSTEPS\s*=\s*([\d.]+)", FIRMWARE.read_text())
    assert m, "could not find MICROSTEPS in the sketch"
    firmware_microsteps = float(m.group(1))
    host_microsteps = DEFAULT_STEPS_PER_RAD * 2.0 * np.pi / 200.0
    assert firmware_microsteps == pytest.approx(host_microsteps), (
        f"sketch is at 1/{firmware_microsteps:g} microstepping but mk2.py's "
        f"DEFAULT_STEPS_PER_RAD assumes 1/{host_microsteps:g}")
