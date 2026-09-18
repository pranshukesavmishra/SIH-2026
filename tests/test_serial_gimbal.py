"""
The Mk1 gimbal driver, exercised without a Nano attached.

Nothing tested this class, because everything it does needs a serial
port. That gap let two real bugs live in it at once: a NameError in
__init__ that made construction impossible, and a laser() that wrote its
command without a newline, so the firmware's line buffer swallowed the
pointing command that followed every toggle.

A fake serial port costs twenty lines and closes the gap.
"""
from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from fsoc_pat.hil.rig import SerialGimbal


class FakePort:
    def __init__(self, *a, **kw):
        self.written = b""

    def write(self, data: bytes) -> int:
        self.written += data
        return len(data)

    def readline(self) -> bytes:
        return b""

    @property
    def lines(self):
        return [l for l in self.written.decode().split("\n") if l]


@pytest.fixture
def gimbal(monkeypatch):
    port = FakePort()
    fake = types.ModuleType("serial")
    fake.Serial = lambda *a, **kw: port
    monkeypatch.setitem(sys.modules, "serial", fake)
    monkeypatch.setattr("time.sleep", lambda *_: None)   # skip the reset wait
    g = SerialGimbal("FAKE")
    g._port = port
    return g


# -- construction --------------------------------------------------------

def test_it_can_be_constructed_at_all(gimbal):
    """Regression: __init__ referenced an undefined name and always raised."""
    assert gimbal.scale == (1.0, 1.0)
    assert gimbal.offset == (0.0, 0.0)


def test_the_scale_argument_is_actually_stored(monkeypatch):
    port = FakePort()
    fake = types.ModuleType("serial")
    fake.Serial = lambda *a, **kw: port
    monkeypatch.setitem(sys.modules, "serial", fake)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    g = SerialGimbal("FAKE", scale=(2.0, 3.0), offset_rad=(0.1, 0.2))
    assert g.scale == (2.0, 3.0)
    assert g.offset == (0.1, 0.2)


# -- the wire ------------------------------------------------------------

def test_every_command_is_newline_terminated(gimbal):
    """
    Regression: laser() wrote b"L1" with no terminator, so the firmware
    held a partial line and ate the front of the next command.
    """
    gimbal.raw_command(90, 90)
    gimbal.laser(True)
    gimbal.raw_command(100, 80)
    gimbal.laser(False)
    gimbal.centre()
    raw = gimbal._port.written.decode()
    assert not raw.replace("\n", "X").endswith("X") or raw.endswith("\n")
    for chunk in raw.split("\n")[:-1]:
        assert chunk, "empty command on the wire"
    assert raw.count("\n") == 5, "one newline per command, no more, no fewer"


def test_a_laser_toggle_does_not_swallow_the_next_pointing_command(gimbal):
    gimbal.laser(True)
    gimbal.raw_command(120, 70)
    assert gimbal._port.lines == ["L1", "P120 T70"]


def test_coarse_commands_are_integers(gimbal):
    """The Mk1 firmware parses %d; a float truncates silently."""
    gimbal.raw_command(91.7, 89.2)
    assert gimbal._port.lines == ["P92 T89"]


def test_commands_are_clamped_to_the_firmware_soft_limits(gimbal):
    gimbal.raw_command(-500, 500)
    pan, tilt = gimbal._port.lines[0].split()
    assert int(pan[1:]) == SerialGimbal.PAN_LIMITS[0]
    assert int(tilt[1:]) == SerialGimbal.TILT_LIMITS[1]


def test_laser_off_and_on_send_the_right_tokens(gimbal):
    gimbal.laser(True); gimbal.laser(False)
    assert gimbal._port.lines == ["L1", "L0"]


# -- the angle convention ------------------------------------------------

def test_centre_commands_ninety_ninety_and_zeroes_the_angles(gimbal):
    gimbal.command(0.3, -0.2)
    gimbal.centre()
    assert gimbal._port.lines[-1] == "P90 T90"
    assert gimbal.reported_pointing() == (0.0, 0.0)


def test_radians_in_degrees_on_the_wire_centred_on_ninety(gimbal):
    gimbal.command(np.radians(10.0), np.radians(-5.0))
    assert gimbal._port.lines[-1] == "P100 T85"


def test_reported_pointing_echoes_the_command_because_servos_have_no_feedback(gimbal):
    gimbal.command(0.05, -0.03)
    assert gimbal.reported_pointing() == (0.05, -0.03)
