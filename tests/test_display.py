"""
The display transform decides whether a person can see anything at all,
and it was wrong in two places at once for months. These tests pin the
properties that were broken.
"""
import numpy as np
import pytest

from fsoc_pat import display


def sky(shape=(480, 640), level=381.0, sigma=10.4, seed=0):
    rng = np.random.default_rng(seed)
    return (rng.normal(level, sigma, shape)).astype(np.float32)


def with_source(peak=2183.0, **kw):
    img = sky(**kw)
    img[240, 320] = peak
    return img


# -- the defect that was there ------------------------------------------

def test_one_hot_pixel_does_not_set_the_scale_for_the_whole_frame():
    """
    The old transform divided by img.max(), so a single saturated pixel
    darkened everything else. The stretch must be robust to that.
    """
    plain = sky()
    hot = plain.copy()
    hot[0, 0] = 4095.0
    a = display.stretch_points(plain)
    b = display.stretch_points(hot)
    assert a[0] == pytest.approx(b[0], rel=1e-3)
    assert a[1] == pytest.approx(b[1], rel=1e-3)


def test_the_sky_lands_at_black_not_at_mid_grey():
    """Measured failure: the old transform put the sky at 231/255."""
    out = display.to_display(sky())
    assert float(np.median(out)) <= 8.0


def test_most_of_the_sky_clamps_to_true_black():
    out = display.to_display(sky())
    assert float((out == 0).mean()) > 0.85


def test_a_point_source_is_clearly_separated_from_the_sky():
    out = display.to_display(with_source())
    assert out[240, 320] > 200
    assert float(np.median(out)) <= 8.0


def test_the_beacon_does_not_saturate_so_its_blink_stays_visible():
    """
    The whole system identifies targets by modulation. A display that
    pins the beacon at 255 hides the one thing a judge needs to see.
    An earlier white point of 40 sigma did exactly that.
    """
    out = display.to_display(with_source())
    assert out[240, 320] < 255, "beacon is clipped; its brightness cannot vary"


def test_a_brightness_change_in_the_beacon_is_actually_rendered():
    pts = display.stretch_points(sky(seed=3))
    dim = display.to_display(with_source(peak=1200.0, seed=3), pts)[240, 320]
    bright = display.to_display(with_source(peak=2183.0, seed=3), pts)[240, 320]
    assert int(bright) - int(dim) > 10, "the blink would be invisible on screen"


def test_a_faint_source_is_still_visible_above_the_noise():
    """A 10-sigma source must not be crushed to black along with the sky."""
    img = sky()
    img[100, 100] = 381.0 + 10 * 10.4
    out = display.to_display(img)
    assert out[100, 100] > 20      # sky renders at 0; this must stand out


# -- properties of the transform ----------------------------------------

def test_output_is_8_bit_and_in_range():
    out = display.to_display(with_source())
    assert out.dtype == np.uint8
    assert out.min() >= 0 and out.max() <= 255


def test_the_transform_is_monotonic():
    """Brighter in must never mean darker out."""
    img = np.linspace(300, 3000, 256, dtype=np.float32).reshape(16, 16)
    out = display.to_display(img)
    flat = out.flatten()
    assert np.all(np.diff(flat.astype(np.int16)) >= 0)


def test_a_flat_frame_does_not_divide_by_zero():
    out = display.to_display(np.full((32, 32), 500.0, dtype=np.float32))
    assert np.isfinite(out).all()


def test_passing_fixed_points_holds_the_stretch_across_frames():
    """
    A stretch recomputed per frame breathes, which hides the brightness
    variation this system identifies targets by.
    """
    pts = display.stretch_points(sky(seed=1))
    dim = with_source(peak=800.0, seed=2)
    bright = with_source(peak=2200.0, seed=2)
    a = display.to_display(dim, pts)[240, 320]
    b = display.to_display(bright, pts)[240, 320]
    assert b > a, "a fixed stretch must still show a brightness change"


def test_smoothing_moves_toward_the_new_value_without_jumping_to_it():
    prev = (100.0, 200.0)
    nxt = (200.0, 400.0)
    got = display.smooth_points(prev, nxt, k=0.12)
    assert prev[0] < got[0] < nxt[0]
    assert prev[1] < got[1] < nxt[1]


def test_smoothing_starts_from_the_first_frame():
    assert display.smooth_points(None, (1.0, 2.0)) == (1.0, 2.0)
