"""
Regression guards for the control loop.

The numbers asserted here were measured on the sterile ramp testbed after the
two-path Smith restructure; a change that quietly reintroduces the
rate-times-latency lag (the bug this file exists because of) fails loudly.
"""
import numpy as np
import pytest

from fsoc_pat import geometry as geo
from fsoc_pat.camera import Gimbal
from fsoc_pat.config import GimbalConfig
from fsoc_pat.control import PointingController


def _ramp(rate_deg_s, seconds=16.0, latency_ms=40.0):
    fps, dt = 30.0, 1.0 / 30.0
    cfg = GimbalConfig(command_latency_ms=latency_ms, encoder_noise_urad=0.0)
    gimbal = Gimbal(cfg, 0.0, 0.3, np.random.default_rng(0))
    ctl = PointingController(cfg, fps, az0=0.0, el0=0.3)
    rate = np.radians(rate_deg_s)
    errors = []
    for i in range(int(seconds * fps)):
        t = i * dt
        err = (geo.wrap_pi(rate * t - gimbal.az), 0.3 - gimbal.el)
        tel = ctl.update(reported=(gimbal.az, gimbal.el), dt=dt,
                         optical_error=err, target_rates=(rate, 0.0))
        gimbal.command(tel.command_az, tel.command_el)
        gimbal.step(dt)
        if t > seconds * 0.6:
            errors.append(geo.wrap_pi(rate * (t + dt) - gimbal.az))
    return np.array(errors) * 1e6                       # urad


def test_ramp_lag_stays_at_the_noise_floor():
    """A step-input Smith structure lags by rate x latency = 524 urad here."""
    lag = _ramp(0.75)
    assert abs(lag.mean()) < 20.0
    assert np.abs(lag).max() < 40.0


def test_fast_ramp_within_the_integral_clamp_regime():
    # The integral path stands in for the follower lag rate^2/(2a) ~ 1.3 mrad
    # at this rate; convergence to that standing value takes ~10 s, so the
    # window is long and the bound reflects the converged behaviour.
    lag = _ramp(3.0, seconds=24.0)
    assert abs(lag.mean()) < 60.0


def test_long_latency_is_still_compensated():
    lag = _ramp(0.75, latency_ms=100.0, seconds=24.0)
    assert abs(lag.mean()) < 40.0


def test_step_settles_without_hunting():
    fps, dt = 30.0, 1.0 / 30.0
    cfg = GimbalConfig(command_latency_ms=40.0, encoder_noise_urad=0.0)
    gimbal = Gimbal(cfg, 0.0, 0.3, np.random.default_rng(0))
    ctl = PointingController(cfg, fps, az0=0.0, el0=0.3)
    target = np.radians(0.3)
    errors = []
    for i in range(int(7.0 * fps)):
        err = (geo.wrap_pi(target - gimbal.az), 0.3 - gimbal.el)
        tel = ctl.update(reported=(gimbal.az, gimbal.el), dt=dt,
                         optical_error=err, target_rates=(0.0, 0.0))
        gimbal.command(tel.command_az, tel.command_el)
        gimbal.step(dt)
        errors.append(abs(err[0]))
    # The mount's discrete-time braking law parks ~42 urad short of any
    # commanded point (measured on the gimbal alone); the integral path
    # removes that bias at its own deliberate pace. So the assertion is
    # two-part: promptly inside the mount's own parking scale, and fully
    # converged once the integrator has had time to work.
    early = np.array(errors[int(2.0 * fps):int(3.0 * fps)]) * 1e6
    late = np.array(errors[int(5.0 * fps):]) * 1e6
    assert early.max() < 200.0
    assert late.max() < 60.0


def test_coasting_returns_last_command_without_input():
    cfg = GimbalConfig()
    ctl = PointingController(cfg, 30.0, az0=0.1, el0=0.2)
    tel = ctl.update(reported=(0.1, 0.2), dt=1 / 30.0)
    assert tel.command_az == pytest.approx(0.1)
    assert tel.command_el == pytest.approx(0.2)


# --- type-2 action against a ramp disturbance --------------------------

def test_the_loop_carries_a_second_integrator():
    """
    PS26169 specifies platform motion as an unmeasured constant-velocity
    disturbance, which is a ramp in position. A single integrator has
    zero steady-state error to a step and a finite, constant error to a
    ramp -- so one integrator is the wrong loop *order* for this input,
    not merely a mistuned one.
    """
    from fsoc_pat.config import GimbalConfig
    c = PointingController(GimbalConfig(), 30.0)
    assert c.kii > 0.0
    assert hasattr(c, "_integral2")


def test_the_second_integrator_leaks():
    """
    A pure double integrator holds its state forever, which is wrong
    twice over here: it overshoots a step (the step-settling test above
    failed the moment this term was added without a leak), and the
    benchmark's drift is bounded so it reverses, after which a wound-up
    term drives the mount the wrong way until it unwinds.
    """
    from fsoc_pat.config import GimbalConfig
    import numpy as np
    c = PointingController(GimbalConfig(), 30.0)
    c._integral2 = np.array([1000.0, 1000.0])
    c._integral = np.zeros(2)
    before = c._integral2.copy()
    for _ in range(60):                       # two seconds of no error
        c.update(reported=(0.0, 0.0), dt=1 / 30.0, optical_error=(0.0, 0.0))
    assert np.all(np.abs(c._integral2) < np.abs(before) * 0.5)


def test_the_integral_clamp_can_hold_the_specified_platform_drift():
    """
    The clamp has to leave room for every *unmeasured* bias the loop
    must hold off, and platform motion is the largest of them. At the
    spec's field of view the benchmark's bounded drift reaches 27,283
    µrad; the clamp was 12,000, sized for the mount's own follower lag
    alone, so the integrator saturated at 44% of what it needed.
    """
    from fsoc_pat.config import GimbalConfig
    c = PointingController(GimbalConfig(), 30.0)
    assert c.integral_limit >= 27283e-6


def test_the_integrator_does_not_wind_during_acquisition():
    """
    The integral path acts on the measured optical error -- the code's
    own comment always said so, and the code did not do it. It wound on
    the filter's encoder-frame fallback too, which is blind to the
    disturbance the integrator exists to cancel and, before a lock
    exists, is computed from a track that may not be the beacon.
    """
    from fsoc_pat.config import GimbalConfig
    import numpy as np
    c = PointingController(GimbalConfig(), 30.0)
    for _ in range(30):
        c.update(reported=(0.0, 0.0), dt=1 / 30.0,
                 optical_error=None, absolute_target=(0.05, 0.05),
                 coasting=False)
    assert np.allclose(c._integral, 0.0)


def test_the_integrator_keeps_working_through_a_confirmed_coast():
    """
    The other half of the same decision. The beacon blinks at 4 Hz with
    a 50% duty cycle against a 30 fps camera, so it is dark in most
    frames by construction; refusing to integrate through the dark phase
    quarters the effective gain and beacon-in-FOV falls from 99% to 65%.
    """
    from fsoc_pat.config import GimbalConfig
    import numpy as np
    c = PointingController(GimbalConfig(), 30.0)
    for _ in range(30):
        c.update(reported=(0.0, 0.0), dt=1 / 30.0,
                 optical_error=None, absolute_target=(0.05, 0.05),
                 coasting=True)
    assert np.any(np.abs(c._integral) > 0.0)
