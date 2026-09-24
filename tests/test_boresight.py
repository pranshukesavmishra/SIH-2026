"""
The dot-tracking loop is the piece that makes Mk3's alignment work without
modelling parallax, so it gets tested against synthetic sources before it
is ever pointed at real hardware.
"""
import math

import numpy as np
import pytest

from fsoc_pat.hil.boresight import (BEACON_HZ, LASER_HZ, BoresightError,
                                    DotClosedLoop, DualFrequencyTracker,
                                    check_frequency_plan)

FPS = 30.0


def square(t, hz, amp=1000.0, floor=50.0):
    """A blinking source's flux: on for half the period, off for half."""
    return floor + (amp if math.sin(2 * math.pi * hz * t) >= 0 else 0.0)


def feed(tracker, frames, sources, fps=FPS):
    """sources: list of (u, v, hz or None). None = steady."""
    for i in range(frames):
        t = i / fps
        dets = []
        for (u, v, hz) in sources:
            flux = square(t, hz) if hz else 900.0
            if flux > 200.0:                     # below this it is not detected
                dets.append((u, v, flux))
        tracker.update(dets)


# -- frequency plan ------------------------------------------------------

def test_frequency_plan_accepts_the_shipped_defaults():
    assert check_frequency_plan(BEACON_HZ, LASER_HZ, FPS, 48) == []


def test_frequency_plan_rejects_aliasing_above_nyquist():
    problems = check_frequency_plan(4.0, 20.0, 30.0, 48)
    assert any("Nyquist" in p for p in problems)


def test_frequency_plan_rejects_frequencies_too_close_to_separate():
    problems = check_frequency_plan(4.0, 4.3, 30.0, 48)
    assert any("apart" in p for p in problems)


def test_frequency_plan_rejects_a_useless_window():
    assert check_frequency_plan(4.0, 7.0, 30.0, 4)


# -- separation ----------------------------------------------------------

def test_beacon_and_dot_are_separated_by_frequency_not_position():
    tr = DualFrequencyTracker(FPS)
    feed(tr, 90, [(300.0, 200.0, BEACON_HZ), (340.0, 230.0, LASER_HZ)])
    err = tr.error()
    assert err.valid, err.reason
    assert not err.merged
    # error points from the dot to the beacon
    assert err.du == pytest.approx(-40.0, abs=1.0)
    assert err.dv == pytest.approx(-30.0, abs=1.0)
    assert err.magnitude_px == pytest.approx(50.0, abs=1.5)


def test_the_brighter_steady_decoy_is_never_taken_for_either_source():
    tr = DualFrequencyTracker(FPS)
    feed(tr, 90, [(300.0, 200.0, BEACON_HZ),
                  (340.0, 230.0, LASER_HZ),
                  (100.0, 100.0, None)])          # steady, and brightest of all
    err = tr.error()
    assert err.valid, err.reason
    assert (err.beacon.u, err.beacon.v) == (300.0, 200.0)
    assert (err.dot.u, err.dot.v) == (340.0, 230.0)


def test_a_lone_steady_source_yields_no_error_and_says_why():
    tr = DualFrequencyTracker(FPS)
    feed(tr, 90, [(100.0, 100.0, None)])
    err = tr.error()
    assert not err.valid
    assert "4 Hz" in err.reason


def test_beacon_without_a_visible_dot_reports_the_laser_missing():
    tr = DualFrequencyTracker(FPS)
    feed(tr, 90, [(300.0, 200.0, BEACON_HZ)])
    err = tr.error()
    assert not err.valid
    assert "laser" in err.reason.lower()


# -- convergence ---------------------------------------------------------

def test_one_source_carrying_both_signatures_counts_as_on_target():
    """
    When the laser lands on the beacon the blobs merge, and a single source
    modulating at both frequencies is success -- not a lost dot.
    """
    tr = DualFrequencyTracker(FPS)
    for i in range(90):
        t = i / FPS
        flux = square(t, BEACON_HZ) + square(t, LASER_HZ)
        tr.update([(300.0, 200.0, flux)])
    err = tr.error()
    assert err.merged
    assert err.converged
    assert err.valid


# -- controller ----------------------------------------------------------

def test_correction_drives_the_dot_toward_the_beacon():
    loop = DotClosedLoop(px_per_rad=(3800.0, 3800.0))
    # beacon is right of and below the dot in image coordinates
    err = BoresightError(du=40.0, dv=30.0,
                         beacon=object(), dot=object(), reason="tracking")
    d_az, d_el = loop.step(err)
    assert d_az > 0                      # pan toward larger u
    assert d_el < 0                      # image v grows downward, so tilt down


def test_corrections_are_clamped_so_one_bad_frame_cannot_fling_the_head():
    loop = DotClosedLoop(px_per_rad=(3800.0, 3800.0), max_step_rad=0.01)
    err = BoresightError(du=50000.0, dv=-50000.0,
                         beacon=object(), dot=object(), reason="tracking")
    d_az, d_el = loop.step(err)
    assert abs(d_az) <= 0.01 + 1e-12
    assert abs(d_el) <= 0.01 + 1e-12


def test_a_dropout_bleeds_the_integral_instead_of_winding_it_up():
    loop = DotClosedLoop(px_per_rad=(3800.0, 3800.0), ki=0.05)
    tracking = BoresightError(du=100.0, dv=0.0,
                              beacon=object(), dot=object(), reason="tracking")
    for _ in range(20):
        loop.step(tracking)
    wound = loop._i_az
    assert wound > 0
    for _ in range(10):
        loop.step(BoresightError(reason="dropout"))
    assert 0 <= loop._i_az < wound


def test_converged_and_merged_means_hold_still():
    loop = DotClosedLoop(px_per_rad=(3800.0, 3800.0))
    err = BoresightError(beacon=object(), dot=object(),
                         merged=True, converged=True)
    assert loop.step(err) == (0.0, 0.0)


def test_camera_roll_is_rotated_out_of_the_error():
    """A camera mounted 90 degrees round must not send pan corrections to tilt."""
    upright = DotClosedLoop(px_per_rad=(3800.0, 3800.0), ki=0.0)
    rolled = DotClosedLoop(px_per_rad=(3800.0, 3800.0), ki=0.0,
                           camera_roll_rad=math.pi / 2)
    err = BoresightError(du=40.0, dv=0.0, beacon=object(), dot=object())
    a_up, e_up = upright.step(err)
    a_ro, e_ro = rolled.step(err)
    assert abs(a_up) > 1e-6 and abs(e_up) < 1e-9
    assert abs(a_ro) < 1e-9 and abs(e_ro) > 1e-6
