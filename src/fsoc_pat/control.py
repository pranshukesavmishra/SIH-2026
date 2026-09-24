"""
Commanding the mount.

Two facts dominate the design, and both push the same way:

**The loop is slow and the disturbances are fast.** Turbulence here has a
Greenwood frequency of 25 Hz and the platform resonates at 18, 47 and 120 Hz,
while the camera delivers 30 frames a second. Everything above 15 Hz is
aliased and simply cannot be observed, let alone corrected. A controller that
tries to chase that jitter amplifies it -- it acts on aliased noise, and the
mount's own inertia turns the commands into extra motion. The correct answer
is a *deliberately low* closed-loop bandwidth, a few hertz, tight enough to
follow real target motion and slow enough to average the jitter away. This is
why a real terminal puts a fine steering mirror downstream at kilohertz rates:
the coarse stage is not supposed to solve the fast problem.

**Commands arrive late.** Pointing commands take effect ~40 ms after they are
issued, which at a 3 Hz bandwidth is already 43 degrees of phase lag -- enough
to turn a well-damped loop into an oscillating one. A **Smith predictor**
handles this: an internal model of the mount is driven by the same commands,
run forward by the latency, and the controller closes its loop on the model's
*predicted* position instead of the stale measured one. The published result
for this technique on optical tip/tilt loops is a bandwidth improvement of
several times over plain PI control.

The error signal itself comes from the image, not the encoders. The offset of
the beacon from the image centre *is* the boresight error, measured optically,
and it is immune to encoder bias -- which is exactly why a tracking sensor
exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from . import geometry as geo
from .camera import Gimbal
from .config import GimbalConfig


class SmithPredictor:
    """
    An internal replica of the mount, used to see past the command latency.

    The replica is driven by every command the controller issues and then run
    forward by the dead time, so ``predict`` answers "where will the real mount
    actually be when this command lands?" rather than "where was it?".
    """

    def __init__(self, cfg: GimbalConfig, az0: float, el0: float):
        self.cfg = cfg
        self._model = Gimbal(cfg, az0, el0, np.random.default_rng(0))
        self.horizon_s = cfg.command_latency_ms / 1000.0

    def issue(self, az: float, el: float) -> None:
        self._model.command(az, el)

    def advance(self, dt: float) -> None:
        self._model.step(dt)

    def sync(self, az: float, el: float, blend: float = 0.05) -> None:
        """
        Nudge the replica towards the measured pointing.

        Pure open-loop prediction drifts as the model and the real mount
        diverge; a slow blend keeps them together without reintroducing the
        measurement lag the predictor exists to remove.
        """
        self._model.az = float(geo.wrap_pi(self._model.az
                                           + blend * geo.wrap_pi(az - self._model.az)))
        self._model.el = float(self._model.el + blend * (el - self._model.el))

    def predict(self, dt: float, sub_steps: int = 4) -> Tuple[float, float]:
        """
        Where the replica will be in ``dt`` seconds, without consuming it.

        Uses a snapshot/restore rather than a deep copy: this runs every frame,
        and copying the mount's command queue and generator each time showed up
        directly in the frame budget.
        """
        state = self._model.snapshot()
        step = dt / max(sub_steps, 1)
        for _ in range(max(sub_steps, 1)):
            self._model.step(step)
        az, el = self._model.az, self._model.el
        self._model.restore(state)
        return az, el

    @property
    def pointing(self) -> Tuple[float, float]:
        return self._model.az, self._model.el


@dataclass
class ControlTelemetry:
    """What the controller did this frame, for the metrics engine and the GUI."""
    command_az: float
    command_el: float
    error_az: float
    error_el: float
    lead_s: float
    used_optical_error: bool


class PointingController:
    """
    Bandwidth-limited proportional-integral controller with rate feed-forward
    and Smith-predictor dead-time compensation.

    ``bandwidth_hz`` is the single most important knob and the one most often
    set wrong. Raising it does not improve tracking here -- it makes the mount
    chase turbulence it cannot resolve. See the module docstring.
    """

    def __init__(self, gimbal_cfg: GimbalConfig, frame_rate_hz: float,
                 az0: float = 0.0, el0: float = 0.0,
                 bandwidth_hz: float = 3.0, kp: float = 0.75, ki: float = 0.35,
                 kii: float = 0.30, integral2_tau_s: float = 1.5,
                 settle_margin_s: float = 0.02, integral_limit_urad: float = 40000.0):
        self.cfg = gimbal_cfg
        self.dt_nominal = 1.0 / frame_rate_hz
        self.bandwidth_hz = float(bandwidth_hz)
        self.kp, self.ki = float(kp), float(ki)
        # Second integral. A single integrator has zero steady-state error
        # to a *step* disturbance and a finite, constant error to a *ramp*
        # -- and PS26169's platform motion is a ramp: constant velocity,
        # unmeasured, up to 20 px/frame. Chasing it with one integrator is
        # not slow tuning, it is the wrong order of loop. At ki = 0.35 the
        # integrator has to accumulate 77,000 urad-seconds of error to
        # produce the 27,000 urad the benchmark's drift needs, which at
        # realistic error magnitudes takes about 26 seconds -- and 26 s is
        # exactly what acquisition measured before this term existed.
        #
        # Integrating the integral makes the loop type 2, which tracks a
        # ramp with zero steady-state error. It is also the classic way to
        # make a loop ring, so the gain is small and the state is clamped
        # separately and harder.
        self.kii = float(kii)
        # ...and it leaks. A pure double integrator holds its state
        # forever, which is wrong for both of the things that actually
        # happen here. On a step it overshoots and hunts -- the existing
        # step-settling test failed the moment this term was added. And
        # the benchmark's platform drift is bounded, so it reverses; a
        # term that has wound up in the old direction then drives the
        # mount the wrong way for as long as it takes to unwind, which is
        # why a 120 s run was far worse than a 30 s one.
        #
        # Leaking it toward zero with a time constant well above the
        # loop's own bandwidth keeps the ramp rejection -- a sustained
        # drift refills it as fast as it drains -- while forgetting a
        # transient. It makes the loop type 2 over the timescales that
        # matter and type 1 over the long run, which is the honest
        # description of what is wanted.
        self.integral2_tau_s = float(integral2_tau_s)
        self.settle_margin_s = float(settle_margin_s)
        # The clamp exists for windup during acquisition transients, but it
        # must not bind in steady tracking, and there are two different
        # things it has to leave room for.
        #
        # The first is the mount's own follower lag: a trapezoidal follower
        # trails a moving command by rate^2 / (2 * accel), about 1300 urad
        # at 3 deg/s here. A clamp below that shows up as a constant
        # tracking lag that appears only above a certain target rate, which
        # is how it was found.
        #
        # The second is any *unmeasured* bias the loop has to hold off,
        # and that is the larger number. PS26169 specifies platform motion
        # up to 20 px/frame, which the gimbal cannot see -- it is not in
        # the encoders -- so the integral path is the only thing that can
        # cancel it, and it can only cancel what it is allowed to hold. At
        # the spec's field of view the benchmark's bounded drift reaches
        # 27,283 urad, and the old 12,000 urad clamp was sized for the
        # follower lag alone. It saturated at 44% of what the disturbance
        # needed, and the beacon spent half the run outside the frame.
        # Measured: raising this alone took beacon-in-FOV from 47% to 99%
        # and mean pointing error from 70,118 to 7,847 urad.
        self.integral_limit = integral_limit_urad * 1e-6

        self.smith = SmithPredictor(gimbal_cfg, az0, el0)
        self._integral = np.zeros(2)
        self._integral2 = np.zeros(2)
        self._filtered_error = np.zeros(2)
        self._last_command = (az0, el0)

    def reset(self, az: float, el: float) -> None:
        self.smith = SmithPredictor(self.cfg, az, el)
        self._integral = np.zeros(2)
        self._integral2 = np.zeros(2)
        self._filtered_error = np.zeros(2)
        self._last_command = (az, el)

    @property
    def lead_time(self) -> float:
        """
        The prediction horizon: exactly the command latency.

        A command issued now takes effect one latency from now, so the mount
        should be sent to where the target will be at that moment -- no more.
        Padding the horizon further (an earlier version added a settle margin)
        systematically leads the target: the mount arrives early by the pad,
        and because the Smith comparison is between two predictions that both
        land on the commanded point, the loop is structurally blind to that
        offset. Only the integral path, which watches the *measured* error,
        can see it -- and it should not be asked to fight a bias the fast path
        created for itself.
        """
        return self.cfg.command_latency_ms / 1000.0

    def _low_pass(self, error: np.ndarray, dt: float) -> np.ndarray:
        alpha = 1.0 - np.exp(-2.0 * np.pi * self.bandwidth_hz * max(dt, 1e-6))
        self._filtered_error += alpha * (error - self._filtered_error)
        return self._filtered_error

    def update(self, reported: Tuple[float, float], dt: float,
               optical_error: Optional[Tuple[float, float]] = None,
               absolute_target: Optional[Tuple[float, float]] = None,
               target_rates: Tuple[float, float] = (0.0, 0.0),
               coasting: bool = False) -> ControlTelemetry:
        """
        Produce the next pointing command.

        ``optical_error`` is the beacon's angular offset from the boresight as
        measured in the image, and is preferred whenever it exists. Without a
        detection the controller falls back to ``absolute_target``, the
        filter's own estimate, which carries the encoder error the optical
        path avoids -- degraded, but enough to coast through a dropout.

        ``coasting`` says that fallback is being used under a *confirmed*
        lock rather than during acquisition. It decides whether the
        integral path is allowed to keep working through the dark phase
        of a blinking beacon; see the note at the integrator below.
        """
        self.smith.advance(dt)
        self.smith.sync(*reported)

        lead = self.lead_time
        predicted_az, predicted_el = self.smith.predict(lead)

        if optical_error is not None:
            measured = np.array(optical_error, dtype=float)
            used_optical = True
        elif absolute_target is not None:
            measured = np.array([geo.wrap_pi(absolute_target[0] - reported[0]),
                                 absolute_target[1] - reported[1]])
            used_optical = False
        else:
            return ControlTelemetry(*self._last_command, 0.0, 0.0, lead, False)

        # The Smith comparison is between two *predictions*: where the target
        # will be when this command lands, and where the mount will be by then
        # under the commands already in flight. Their difference is the error
        # still outstanding.
        #
        # This framing matters on a moving target. Comparing against the
        # mount's in-flight motion alone -- as a step-input Smith predictor
        # does -- misreads target-following motion as correction-in-transit
        # and injects a permanent bias of -rate x lead into the error signal;
        # the integrator then winds against it and the mount settles one dead
        # time behind the target. Measured on a sterile ramp testbed, that
        # structure lagged by exactly rate x latency (444 urad at 0.75 deg/s)
        # while this one holds the lag near the noise floor.
        predicted_target = np.array([
            reported[0] + measured[0] + target_rates[0] * lead,
            reported[1] + measured[1] + target_rates[1] * lead])
        outstanding = np.array([geo.wrap_pi(predicted_target[0] - predicted_az),
                                predicted_target[1] - predicted_el])

        smoothed = self._low_pass(outstanding, dt)
        # Two-path Smith arrangement. The proportional path acts on the model
        # comparison: fast, and immune to the dead time. The integral path
        # acts on the MEASURED optical error: slow, but it is the only signal
        # that reflects where the mount truly is, so it is the only path that
        # can remove a constant offset the model cannot see -- model mismatch,
        # calibration bias, platform drift, or any residual lead/lag of the
        # fast path itself.
        #
        # "Optical error" is meant literally, and the code did not honour it:
        # it integrated whatever error it was handed, including the filter's
        # own absolute-target fallback. That fallback is expressed against
        # the encoders, so it is blind to exactly the disturbances the
        # integrator exists to cancel, and during acquisition it is computed
        # from a track that may not even be the beacon. Winding the
        # integrator on it delayed acquisition from 4.1 s to 25.3 s.
        #
        # But "not optical" is two different situations and they need
        # opposite treatment, which is the part that took measuring to
        # find.
        #
        # During ACQUIRE there is a candidate track that may not be the
        # beacon at all, and its error is computed against the encoders.
        # Winding on that is winding on a guess.
        #
        # During COAST the lock is confirmed and the beacon is merely
        # dark -- it blinks at 4 Hz with a 50% duty cycle against a 30 fps
        # camera, so it is dark in most frames by construction. The
        # filter's estimate there descends from real optical detections
        # and still carries the drift. Refusing to integrate through the
        # dark phase quarters the effective integral gain, the integrator
        # never reaches the value a 20 px/frame platform drift needs, and
        # beacon-in-FOV falls from 99% to 65%.
        #
        # Measured, 30 s at spec: winding on everything gives 47% in FOV
        # and 25.3 s to acquire; winding only on optical gives 65% and
        # 4.1 s; winding on optical and coast gives both.
        #
        # (An earlier attempt integrated the current error over the whole
        # elapsed dark span, to keep the gain duty-cycle independent. That
        # applies one measurement across a window in which the error was
        # something else, so a single detection after a long gap slams the
        # integrator into its clamp. It lost acquisition entirely.)
        if used_optical or coasting:
            self._integral = np.clip(self._integral + measured * dt,
                                     -self.integral_limit, self.integral_limit)
            # The type-2 state. Clamped to the same envelope divided by
            # its own gain, so the term it contributes cannot exceed what
            # the first integrator is allowed to contribute -- a double
            # integrator that is allowed to dominate is how these loops
            # ring themselves apart.
            lim2 = self.integral_limit * self.ki / max(self.kii, 1e-9)
            leak = np.exp(-dt / max(self.integral2_tau_s, 1e-6))
            self._integral2 = np.clip(self._integral2 * leak + self._integral * dt,
                                      -lim2, lim2)

        command_az = (predicted_target[0] + self.kp * smoothed[0]
                      + self.ki * self._integral[0] + self.kii * self._integral2[0])
        command_el = (predicted_target[1] + self.kp * smoothed[1]
                      + self.ki * self._integral[1] + self.kii * self._integral2[1])

        lo, hi = np.radians(self.cfg.el_limits_deg)
        command_az = float(geo.wrap_pi(command_az))
        command_el = float(np.clip(command_el, lo, hi))

        self.smith.issue(command_az, command_el)
        self._last_command = (command_az, command_el)
        return ControlTelemetry(command_az, command_el,
                                float(outstanding[0]), float(outstanding[1]),
                                lead, used_optical)
