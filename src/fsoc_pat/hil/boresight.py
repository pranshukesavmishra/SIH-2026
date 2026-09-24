"""
Closing the alignment loop on the laser's own dot.

The Mk3 terminal carries its camera on the gimbal, boresighted with the
laser, so the camera sees the beacon *and* the terminal's own laser dot.
That is what this module exploits, and it removes the hardest problem in
the build.

Camera and laser cannot occupy the same point in space, so "beacon
centred in the image" is not "laser on the beacon". The offset between
them is parallax, and it scales as separation/range: with 20 mm between
the optical axes, it is 33 mrad at 0.6 m and 4 mrad at 5 m, against a
pointing budget of roughly 1 mrad. Parallax is not a correction here --
at close range it is the entire error budget, several times over.

Every approach that *models* it loses. Calibrate a fixed offset and it is
wrong at every range but one. Estimate the range and you have added a
range estimator to the error chain. Measure the baseline and mount flex
and thermal drift walk away from your number over an afternoon.

So this module does not model it. The beacon modulates at 4 Hz, the laser
at 7 Hz, both are identified by frequency in the same image, and the
control error is the pixel vector from the dot to the beacon. Parallax,
boresight misalignment, mount flex, thermal drift and range all cancel
identically, because every one of them displaces the dot and the loop is
closed on the dot.

The same principle as the rest of the system, applied to ourselves:
brightness is not identity, modulation is.
"""
from __future__ import annotations

import collections
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..tracking import goertzel_power

#: Default modulation assignments. They must differ by several Goertzel
#: bins and both sit below Nyquist for the frame rate in use -- see
#: `check_frequency_plan`, which is not optional at bring-up.
BEACON_HZ = 4.0
LASER_HZ = 7.0


@dataclass
class Source:
    """One persistent bright point in the image, and its flux history."""
    source_id: int
    u: float
    v: float
    flux_history: collections.deque = field(default_factory=lambda:
                                            collections.deque(maxlen=64))
    misses: int = 0
    beacon_score: float = 0.0
    laser_score: float = 0.0

    @property
    def samples(self) -> int:
        return len(self.flux_history)


@dataclass
class BoresightError:
    """
    The fine-alignment error, in pixels, pointing from the dot to the beacon.

    `converged` is deliberately not "the error is small". When the laser
    lands on the beacon the two sources merge into one blob, and a single
    source scoring at *both* frequencies is the unambiguous signature of
    success -- there is no pixel gap left to measure. Treating a vanished
    dot as "error unknown" would make the loop give up exactly when it had
    won.
    """
    du: float = 0.0
    dv: float = 0.0
    beacon: Optional[Source] = None
    dot: Optional[Source] = None
    converged: bool = False
    merged: bool = False
    reason: str = ""

    @property
    def magnitude_px(self) -> float:
        return math.hypot(self.du, self.dv)

    @property
    def valid(self) -> bool:
        return self.beacon is not None and (self.dot is not None or self.merged)


def check_frequency_plan(beacon_hz: float, laser_hz: float,
                         frame_rate: float, window: int) -> List[str]:
    """
    Reasons the chosen frequencies will not work at this frame rate.

    Returns an empty list when the plan is sound. Call it at bring-up: a
    frequency plan that aliases produces a loop that looks like it is
    running and is in fact scoring noise, which is far more expensive to
    diagnose on a bench than one line at startup.
    """
    problems: List[str] = []
    nyquist = frame_rate / 2.0
    for name, hz in (("beacon", beacon_hz), ("laser", laser_hz)):
        if hz <= 0:
            problems.append(f"{name} frequency must be positive")
        elif hz >= nyquist:
            problems.append(
                f"{name} at {hz:g} Hz is at or above Nyquist ({nyquist:g} Hz) "
                f"for {frame_rate:g} fps -- it will alias")
    if window < 8:
        problems.append(f"window of {window} frames is too short to resolve any frequency")
        return problems
    bin_hz = frame_rate / window
    separation = abs(beacon_hz - laser_hz)
    if separation < 2.0 * bin_hz:
        problems.append(
            f"beacon and laser are {separation:g} Hz apart, under two Goertzel "
            f"bins ({2 * bin_hz:.2f} Hz at {frame_rate:g} fps / {window} frames) "
            f"-- they will not separate cleanly")
    return problems


class DualFrequencyTracker:
    """
    Associates bright points across frames and scores each at both frequencies.

    Deliberately simple association -- nearest neighbour inside a gate.
    The full IMM/JPDA machinery in `tracking.py` exists to hold tracks
    through occlusion and clutter across a wide sky; here there are two or
    three near-stationary sources in a narrow FOV, and borrowing that
    complexity would add failure modes without buying anything.
    """

    def __init__(self, frame_rate: float,
                 beacon_hz: float = BEACON_HZ,
                 laser_hz: float = LASER_HZ,
                 window: int = 48,
                 gate_px: float = 25.0,
                 min_score: float = 0.25,
                 max_misses: int = 12):
        self.frame_rate = float(frame_rate)
        self.beacon_hz = float(beacon_hz)
        self.laser_hz = float(laser_hz)
        self.window = int(window)
        self.gate_px = float(gate_px)
        self.min_score = float(min_score)
        self.max_misses = int(max_misses)
        self.sources: Dict[int, Source] = {}
        self._next_id = 0

    # -- association ------------------------------------------------------

    def update(self, detections: Sequence[Tuple[float, float, float]]) -> None:
        """Feed one frame's detections as (u, v, flux) triples."""
        unmatched = list(detections)
        for src in self.sources.values():
            best, best_d = None, self.gate_px
            for det in unmatched:
                d = math.hypot(det[0] - src.u, det[1] - src.v)
                if d < best_d:
                    best, best_d = det, d
            if best is None:
                src.misses += 1
                # A source that blinks is absent for half its period by
                # construction. Carrying a zero keeps the Goertzel window
                # phase-correct; skipping the frame would smear it.
                src.flux_history.append(0.0)
            else:
                src.misses = 0
                src.u, src.v = best[0], best[1]
                src.flux_history.append(float(best[2]))
                unmatched.remove(best)

        for det in unmatched:
            src = Source(source_id=self._next_id, u=det[0], v=det[1],
                         flux_history=collections.deque(maxlen=max(self.window, 8)))
            src.flux_history.append(float(det[2]))
            self.sources[self._next_id] = src
            self._next_id += 1

        for sid in [s for s, src in self.sources.items()
                    if src.misses > self.max_misses]:
            del self.sources[sid]

        self._score()

    def _score(self) -> None:
        nb = self.beacon_hz / self.frame_rate
        nl = self.laser_hz / self.frame_rate
        for src in self.sources.values():
            hist = list(src.flux_history)
            src.beacon_score = goertzel_power(hist, nb)
            src.laser_score = goertzel_power(hist, nl)

    # -- interpretation ---------------------------------------------------

    def error(self, merge_px: float = 12.0) -> BoresightError:
        """
        Current dot-to-beacon pixel error, or why there isn't one.
        """
        ready = [s for s in self.sources.values() if s.samples >= max(16, self.window // 3)]
        if not ready:
            return BoresightError(reason="no source has enough history yet")

        beacon = max(ready, key=lambda s: s.beacon_score)
        if beacon.beacon_score < self.min_score:
            return BoresightError(
                reason=f"no source modulating at {self.beacon_hz:g} Hz "
                       f"(best score {beacon.beacon_score:.2f})")

        # Success case first: one source carrying both signatures is the dot
        # sitting on the beacon, not a missing dot.
        if beacon.laser_score >= self.min_score:
            return BoresightError(beacon=beacon, dot=beacon, converged=True,
                                  merged=True,
                                  reason="dot and beacon merged -- on target")

        others = [s for s in ready if s is not beacon]
        if not others:
            return BoresightError(beacon=beacon,
                                  reason="beacon found, laser dot not visible "
                                         "-- is the laser on and in frame?")

        dot = max(others, key=lambda s: s.laser_score)
        if dot.laser_score < self.min_score:
            return BoresightError(beacon=beacon,
                                  reason=f"no source modulating at {self.laser_hz:g} Hz "
                                         f"(best score {dot.laser_score:.2f}); "
                                         f"a steady bright source here is the decoy")

        du, dv = beacon.u - dot.u, beacon.v - dot.v
        return BoresightError(du=du, dv=dv, beacon=beacon, dot=dot,
                              converged=math.hypot(du, dv) <= merge_px,
                              reason="tracking")


class DotClosedLoop:
    """
    Turns a dot-to-beacon pixel error into a gimbal correction, in radians.

    Proportional with a light integral term. No derivative: the error
    signal is a pixel centroid of a blinking source, which is exactly the
    kind of quantised, intermittently-updated measurement that a
    derivative term amplifies into dither.

    `px_per_rad` comes from calibration, not from the lens datasheet.
    """

    def __init__(self, px_per_rad: Tuple[float, float],
                 kp: float = 0.35, ki: float = 0.05,
                 max_step_rad: float = 0.02,
                 integral_limit_rad: float = 0.01,
                 camera_roll_rad: float = 0.0):
        self.px_per_rad = px_per_rad
        self.kp = kp
        self.ki = ki
        self.max_step_rad = max_step_rad
        self.integral_limit_rad = integral_limit_rad
        self.camera_roll_rad = camera_roll_rad
        self._i_az = 0.0
        self._i_el = 0.0

    def reset(self) -> None:
        self._i_az = self._i_el = 0.0

    def step(self, err: BoresightError) -> Tuple[float, float]:
        """Correction to add to the current pointing, radians (az, el)."""
        if not err.valid or err.merged:
            # Hold, and bleed the integral down rather than letting it sit
            # wound up through a dropout and kick on reacquisition.
            self._i_az *= 0.9
            self._i_el *= 0.9
            return 0.0, 0.0

        du, dv = err.du, err.dv
        if self.camera_roll_rad:
            c, s = math.cos(-self.camera_roll_rad), math.sin(-self.camera_roll_rad)
            du, dv = c * du - s * dv, s * du + c * dv

        e_az = du / self.px_per_rad[0]
        e_el = -dv / self.px_per_rad[1]      # image v grows downward

        self._i_az = float(np.clip(self._i_az + self.ki * e_az,
                                   -self.integral_limit_rad, self.integral_limit_rad))
        self._i_el = float(np.clip(self._i_el + self.ki * e_el,
                                   -self.integral_limit_rad, self.integral_limit_rad))

        d_az = self.kp * e_az + self._i_az
        d_el = self.kp * e_el + self._i_el
        lim = self.max_step_rad
        return float(np.clip(d_az, -lim, lim)), float(np.clip(d_el, -lim, lim))
