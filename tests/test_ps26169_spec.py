"""
The problem statement's Parameters and Specifications table, as tests.

PS26169 publishes a table of numbers the system is benchmarked against.
Reading that table and believing our software already complied with it
is how a team discovers on demo day that its acquisition figures were
measured with a mount four times faster than the rules allow -- which is
exactly what had happened here before these tests existed.

So each row of the table that we can check statically is checked here,
against ``scenarios/ps26169_benchmark.yaml``. The point is not that the
file is correct today; it is that nobody can quietly widen the field of
view or raise the slew rate to make a number look better without a test
turning red.
"""
from __future__ import annotations

import math
import pathlib

import numpy as np
import pytest

from fsoc_pat import atmosphere
from fsoc_pat.beacon import Beacon, _GENERATORS
from fsoc_pat.camera import Detector
from fsoc_pat.config import BeaconConfig, CameraConfig, SimConfig, TrajectoryConfig
from fsoc_pat.optics import splat_gaussian, splat_square

SCENARIO = pathlib.Path(__file__).resolve().parents[1] / "scenarios" / "ps26169_benchmark.yaml"


@pytest.fixture(scope="module")
def cfg():
    return SimConfig.load(str(SCENARIO))


# --- the specification table -------------------------------------------

def test_camera_resolution_is_the_specified_640x480(cfg):
    assert (cfg.camera.width, cfg.camera.height) == (640, 480)


def test_horizontal_field_of_view_is_the_specified_4_degrees(cfg):
    assert cfg.camera.fov_deg == pytest.approx(4.0)


def test_vertical_field_of_view_follows_at_the_specified_3_degrees(cfg):
    """
    The spec gives 4x3 deg and a 640x480 sensor. Those are only
    consistent if the pixels are square, so check that they are: a
    vertical FOV that came out at anything but 3 deg would mean we had
    misread the table or the sensor aspect.
    """
    half_h = math.radians(cfg.camera.fov_deg) / 2.0
    half_v = math.atan(math.tan(half_h) * cfg.camera.height / cfg.camera.width)
    assert math.degrees(2.0 * half_v) == pytest.approx(3.0, abs=0.01)


def test_pan_tilt_rate_is_inside_the_specified_5_to_10_deg_per_second(cfg):
    """
    The row that invalidated our published acquisition times. Our other
    scenarios run at 20 deg/s; the spec's default is 5 and its ceiling is
    10. A faster mount finds the target sooner, so benchmarking above the
    ceiling measures a system the evaluators are not being offered.
    """
    assert 5.0 <= cfg.gimbal.max_rate_deg_s <= 10.0


def test_frame_rate_meets_the_specified_20_fps_floor(cfg):
    assert cfg.camera.frame_rate_hz >= 20.0


def test_target_is_a_square_inside_the_specified_5_to_20_px_range(cfg):
    beacon = cfg.beacons[0]
    assert beacon.size_px == pytest.approx(10.0)
    assert 5.0 <= beacon.size_px <= 20.0


def test_salt_and_pepper_noise_is_enabled_in_the_benchmark(cfg):
    assert cfg.camera.salt_pepper_fraction > 0.0


def test_benchmark_target_moves_on_the_mandatory_figure_of_eight(cfg):
    assert cfg.beacons[0].trajectory.kind == "figure_eight"


def test_at_least_four_motion_patterns_are_available(cfg):
    """Spec: >= 4 motion patterns, Figure-of-8 among them."""
    assert "figure_eight" in _GENERATORS
    assert len(_GENERATORS) >= 4


# --- figure-of-eight geometry ------------------------------------------

def _fig8(period=40.0, width=2.0, height=1.0):
    cfg = BeaconConfig(trajectory=TrajectoryConfig(
        kind="figure_eight",
        params={"center_az_deg": 0.0, "center_el_deg": 20.0,
                "width_deg": width, "height_deg": height, "period_s": period}))
    return Beacon(cfg, np.random.default_rng(0))


def test_figure_eight_closes_on_itself_after_one_period():
    b = _fig8()
    a0 = np.array(b.state(0.0)[:2])
    a1 = np.array(b.state(40.0)[:2])
    assert np.allclose(a0, a1, atol=1e-12)


def test_figure_eight_crosses_itself_at_the_centre():
    """
    The defining property, and the reason the spec asks for this shape:
    the target passes through one point twice per period travelling in
    two different directions. A filter that has learned a velocity at the
    first crossing predicts the wrong thing at the second.
    """
    b = _fig8()
    centre = np.radians([0.0, 20.0])
    at_0 = np.array(b.state(0.0)[:2])
    at_half = np.array(b.state(20.0)[:2])
    assert np.allclose(at_0, centre, atol=1e-12)
    assert np.allclose(at_half, centre, atol=1e-12)

    eps = 0.01
    v0 = np.array(b.state(eps)[:2]) - at_0
    v1 = np.array(b.state(20.0 + eps)[:2]) - at_half
    # Same point, opposite azimuth travel -- so it is a crossing, not a
    # retrace of the same lobe.
    assert np.sign(v0[0]) == -np.sign(v1[0])


def test_figure_eight_elevation_excursion_matches_the_configured_height():
    """
    ``height_deg`` has to mean the excursion a user measures on screen.
    max(sin x cos x) is 1/2, so without the factor of two inside the
    generator this would silently come out half the requested size.
    """
    b = _fig8(height=1.0)
    ts = np.linspace(0.0, 40.0, 4001)
    el = np.degrees([b.state(t)[1] for t in ts]) - 20.0
    assert el.max() == pytest.approx(1.0, abs=1e-3)
    assert el.min() == pytest.approx(-1.0, abs=1e-3)


def test_figure_eight_reverses_elevation_acceleration_four_times():
    """What makes it the manoeuvre test rather than another circle."""
    b = _fig8()
    # Sample just past one full period, so the reversal at the closure
    # point is inside the window. Stopping exactly at t = period finds
    # only three, because the fourth happens on the wrap.
    ts = np.linspace(0.0, 40.2, 2011)
    el = np.array([b.state(t)[1] for t in ts])
    accel = np.diff(el, n=2)
    # Count genuine flips only. np.sign is 0 at an exact crossing, and a
    # +1 -> 0 -> -1 run reads as two changes if the zeros are kept --
    # which is why a first version of this test claimed six.
    signs = np.sign(accel)
    signs = signs[signs != 0]
    sign_changes = int((np.diff(signs) != 0).sum())
    assert sign_changes == 4


# --- salt and pepper ----------------------------------------------------

def _detector(fraction):
    cfg = CameraConfig(width=64, height=64, salt_pepper_fraction=fraction,
                       hot_pixel_fraction=0.0, read_noise_e=0.0,
                       dark_current_e_per_s=0.0)
    return cfg, Detector(cfg, np.random.default_rng(3))


def test_salt_and_pepper_is_off_by_default():
    """Every existing scenario must render exactly as it did before."""
    assert CameraConfig().salt_pepper_fraction == 0.0


def test_salt_and_pepper_puts_pixels_at_both_rails():
    cfg, det = _detector(0.05)
    mid = np.full((64, 64), cfg.full_well_e / 2.0 / (cfg.exposure_ms / 1000.0))
    frame = det.expose(mid)
    assert (frame == det.max_dn).sum() > 0
    assert (frame == 0).sum() > 0


def test_salt_and_pepper_hits_about_the_requested_fraction():
    cfg, det = _detector(0.05)
    mid = np.full((64, 64), cfg.full_well_e / 2.0 / (cfg.exposure_ms / 1000.0))
    frame = det.expose(mid)
    hit = ((frame == det.max_dn) | (frame == 0)).sum()
    assert hit == pytest.approx(0.05 * frame.size, rel=0.05)


def test_salt_and_pepper_moves_between_frames():
    """
    The property that separates it from a hot pixel. Hot pixels sit
    still and a dark frame removes them; impulse noise does not, which is
    the whole reason the spec lists it separately.
    """
    cfg, det = _detector(0.02)
    mid = np.full((64, 64), cfg.full_well_e / 2.0 / (cfg.exposure_ms / 1000.0))
    a = det.expose(mid) == det.max_dn
    b = det.expose(mid) == det.max_dn
    assert a.sum() > 0 and b.sum() > 0
    assert (a & b).sum() < 0.2 * a.sum()


def test_salt_and_pepper_never_exceeds_the_bit_depth():
    cfg, det = _detector(0.1)
    mid = np.full((64, 64), cfg.full_well_e / 2.0 / (cfg.exposure_ms / 1000.0))
    frame = det.expose(mid)
    assert frame.max() <= det.max_dn
    assert frame.dtype == np.uint16


# --- the resolved square target ----------------------------------------

def test_square_target_conserves_total_flux():
    """
    Photometry must not depend on shape: the same beacon given a size has
    to deliver the same number of electrons, or every SNR number in the
    report becomes shape-dependent and incomparable.
    """
    img = np.zeros((96, 96))
    splat_square(img, 48.0, 48.0, 1000.0, 10.0, 1.3)
    assert img.sum() == pytest.approx(1000.0, rel=1e-6)


def test_square_target_spreads_flux_so_the_peak_pixel_collapses():
    """
    The reason the spec's shape matters. Same flux, ~8x lower peak -- a
    detector thresholding on peak brightness fails on the spec's target
    while passing on a point source.
    """
    point = np.zeros((96, 96))
    square = np.zeros((96, 96))
    splat_gaussian(point, 48.0, 48.0, 1000.0, 1.3)
    splat_square(square, 48.0, 48.0, 1000.0, 10.0, 1.3)
    assert square.max() < point.max() / 5.0


def test_square_target_is_actually_square_not_round():
    img = np.zeros((96, 96))
    splat_square(img, 48.0, 48.0, 1000.0, 20.0, 0.5)
    lit = img > img.max() * 0.5
    rows = np.where(lit.any(axis=1))[0]
    cols = np.where(lit.any(axis=0))[0]
    height = rows[-1] - rows[0] + 1
    width = cols[-1] - cols[0] + 1
    assert height == pytest.approx(width, abs=1)
    # A disc of this width would fill pi/4 = 79% of its bounding box; a
    # square fills all of it.
    assert lit.sum() > 0.95 * height * width


def test_zero_size_still_renders_the_point_source_exactly():
    """Existing scenarios must be bit-identical, not merely similar."""
    a = np.zeros((64, 64))
    b = np.zeros((64, 64))
    splat_gaussian(a, 32.3, 31.7, 500.0, 1.3)
    splat_square(b, 32.3, 31.7, 500.0, 0.0, 1.3)
    assert np.array_equal(a, b)


# --- atmospheric conditions --------------------------------------------

def test_all_five_specified_conditions_exist():
    assert set(atmosphere.PRESETS) == {"clear", "haze", "fog", "rain", "low_light"}


def test_applying_a_condition_does_not_mutate_the_original(cfg):
    before = cfg.beacons[0].amplitude_e_s
    atmosphere.apply(cfg, "fog")
    assert cfg.beacons[0].amplitude_e_s == before


def test_fog_takes_signal_and_adds_background(cfg):
    """Fog hurts twice. A model that only dimmed the beacon would be wrong."""
    fog = atmosphere.apply(cfg, "fog")
    assert fog.beacons[0].amplitude_e_s < cfg.beacons[0].amplitude_e_s
    assert fog.scene.sky_brightness_e_s > cfg.scene.sky_brightness_e_s


def test_rain_adds_clutter_rather_than_removing_it(cfg):
    """
    Drops crossing the field make bright point-like transients, so rain
    is a discrimination problem. Fog, which washes them out, is not.
    """
    rain = atmosphere.apply(cfg, "rain")
    fog = atmosphere.apply(cfg, "fog")
    assert rain.scene.clutter_count > cfg.scene.clutter_count
    assert fog.scene.clutter_count < cfg.scene.clutter_count


def test_low_light_darkens_the_sky_but_not_the_active_beacon(cfg):
    """The argument for an active beacon, stated as a test."""
    dusk = atmosphere.apply(cfg, "low_light")
    assert dusk.scene.sky_brightness_e_s < cfg.scene.sky_brightness_e_s
    assert dusk.beacons[0].amplitude_e_s == cfg.beacons[0].amplitude_e_s


def test_clear_leaves_the_scenario_alone(cfg):
    clear = atmosphere.apply(cfg, "clear")
    assert clear.beacons[0].amplitude_e_s == cfg.beacons[0].amplitude_e_s
    assert clear.scene.sky_brightness_e_s == cfg.scene.sky_brightness_e_s


def test_blur_adds_in_quadrature_not_linearly(cfg):
    """Independent Gaussians; adding sigmas would overstate fog by ~40%."""
    fog = atmosphere.apply(cfg, "fog")
    expected = math.hypot(cfg.turbulence.seeing_blur_px, atmosphere.PRESETS["fog"]["blur_px"])
    assert fog.turbulence.seeing_blur_px == pytest.approx(expected)


def test_an_unknown_condition_is_refused_by_name(cfg):
    with pytest.raises(ValueError, match="unknown atmospheric condition"):
        atmosphere.apply(cfg, "drizzle")


def test_condition_names_are_accepted_in_the_spellings_a_user_types(cfg):
    for spelling in ("Low Light", "low-light", "LOW_LIGHT", " fog "):
        atmosphere.apply(cfg, spelling)


# --- rows read properly the second time --------------------------------

def test_salt_and_pepper_is_the_specified_ten_percent(cfg):
    """
    The spec says "around 10% of image". This file first carried 0.001 --
    a hundred times too little -- because the figure was taken from a
    summary rather than the table. At 0.001 the rejection worked in one
    pass; at 0.1 it needed to iterate, and the single-pass version left
    1,689 pepper pixels and made the detector worse than useless.
    """
    assert cfg.camera.salt_pepper_fraction == pytest.approx(0.10)


def test_camera_starts_at_the_centre_of_the_screen(cfg):
    """
    Spec row 6. The target's start is offset from it, so acquisition is a
    real search rather than a target already in frame.
    """
    assert tuple(cfg.initial_pointing_deg) == (0.0, 20.0)
    params = cfg.beacons[0].trajectory.params
    assert (params["center_az_deg"], params["center_el_deg"]) != (0.0, 20.0)


def test_the_search_covers_the_whole_screen(cfg):
    """
    2000 px of screen at the camera's own 0.00625 deg/px is 12.5 deg, so
    the half-diagonal is 8.84 deg and the field of uncertainty has to be
    at least the half-width. A smaller one would quietly assume the
    target starts near the middle.
    """
    assert cfg.acquisition_fou_deg >= 6.25


def test_the_specs_own_numbers_are_self_consistent():
    """
    Not a test of our code -- a test of our reading of the spec, which is
    worth pinning because it is what the whole benchmark rests on. If
    2000 px of screen spans 12.5 deg at the camera's resolution, then a
    5 deg/s mount crosses the half-diagonal in under the 2 s acquisition
    limit. Three independent rows of the table agreeing is how we know
    the interpretation is right.
    """
    deg_per_px = 4.0 / 640.0
    screen_deg = 2000 * deg_per_px
    assert screen_deg == pytest.approx(12.5)
    half_diagonal = math.hypot(screen_deg / 2, screen_deg / 2)
    assert half_diagonal / 5.0 < 2.0


def test_platform_motion_is_linear_and_mandatory(cfg):
    """
    Spec: platform motion, "Default/Mandatory: Linear". An earlier
    version modelled it as a 0.7 Hz oscillation, which is not linear and
    is a different control problem -- an oscillation averages to zero
    over its period and a drift never does, so one can be filtered and
    the other has to be nulled.
    """
    assert cfg.vibration.platform_drift_urad_s > 0.0


def test_platform_drift_stays_inside_the_specified_20_px_per_frame(cfg):
    """20 px/frame is the ceiling, and it is a severe one."""
    focal = 320.0 / math.tan(math.radians(cfg.camera.fov_deg / 2))
    px_per_frame = (cfg.vibration.platform_drift_urad_s * 1e-6
                    * focal / cfg.camera.frame_rate_hz)
    assert 0.0 < px_per_frame <= 20.0


def test_platform_drift_is_bounded_so_a_long_run_stays_on_screen(cfg):
    assert cfg.vibration.platform_drift_limit_urad > 0.0


def test_all_four_mandatory_motion_patterns_exist():
    """Spec: "at least four: Straight Line, Circular, Figure of 8, Random"."""
    for kind in ("linear", "circular", "figure_eight", "random_walk"):
        assert kind in _GENERATORS, f"{kind} is one of the four the spec names"


def test_the_report_states_tracking_error_in_pixels_too():
    """
    The spec's tracking limit is 10 pixels and both benchmark stages are
    scored on centroiding error, a pixel quantity. A report in
    microradians alone leaves the evaluator converting our numbers
    against a threshold written in the other unit.
    """
    from fsoc_pat.metrics import PerformanceReport
    r = PerformanceReport(scenario_name="x")
    assert hasattr(r, "tracking_error_px") and hasattr(r, "pointing_error_px")


def test_pixel_error_is_the_focal_length_times_the_angle():
    from fsoc_pat.metrics import build_report
    from fsoc_pat.pipeline import LockState

    class T:
        def __init__(self):
            self.time_s = 0.0
            self.processing_ms = 1.0
            self.locked = True
            self.detected = True
            self.beacon_in_fov = True
            self.n_detections = 1
            self.state = LockState.TRACK
            self.on_decoy = False
            self.truth_error_rad = 109.13e-6      # exactly one pixel at 4 deg
            self.pointing_error_rad = 109.13e-6

    focal = 320.0 / math.tan(math.radians(2.0))
    r = build_report([T()], "x", 30.0, focal_px=focal)
    assert r.tracking_error_px["mean"] == pytest.approx(1.0, abs=0.01)


def test_pixel_error_is_left_empty_when_the_optics_are_unknown():
    """A conversion without a focal length would be a guess."""
    from fsoc_pat.metrics import PerformanceReport
    assert PerformanceReport(scenario_name="x").tracking_error_px == {}
