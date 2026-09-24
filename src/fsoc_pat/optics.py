"""
Shared rendering primitive: splatting point sources onto the focal plane.

Beacons, stars, clutter and sun glint are all unresolved point sources, so
they all reach the detector as the same thing — the point spread function,
scaled by brightness. Rendering them through one function keeps them
photometrically consistent, which matters: if clutter were drawn differently
from the beacon, a detector could cheat by learning the difference.
"""
from __future__ import annotations

import numpy as np


def splat_gaussian(image: np.ndarray, u: float, v: float, amplitude: float,
                   sigma: float, extent_sigmas: float = 4.0) -> None:
    """
    Add one Gaussian PSF to ``image`` in place, at sub-pixel position (u, v).

    Only a local window is touched, so rendering a thousand stars costs
    milliseconds rather than a full-frame operation each.
    """
    if amplitude <= 0.0 or sigma <= 0.0:
        return
    height, width = image.shape
    radius = int(np.ceil(extent_sigmas * sigma))

    u0, u1 = int(np.floor(u)) - radius, int(np.floor(u)) + radius + 1
    v0, v1 = int(np.floor(v)) - radius, int(np.floor(v)) + radius + 1
    u0c, u1c = max(u0, 0), min(u1, width)
    v0c, v1c = max(v0, 0), min(v1, height)
    if u0c >= u1c or v0c >= v1c:
        return

    xs = np.arange(u0c, u1c, dtype=np.float32) + np.float32(0.5 - u)
    ys = np.arange(v0c, v1c, dtype=np.float32) + np.float32(0.5 - v)
    gx = np.exp(-0.5 * (xs / sigma) ** 2)
    gy = np.exp(-0.5 * (ys / sigma) ** 2)
    # Normalised so `amplitude` is total signal, not peak: brightness then
    # stays meaningful when the PSF widens under seeing.
    kernel = np.outer(gy, gx) / np.float32(2.0 * np.pi * sigma * sigma)
    image[v0c:v1c, u0c:u1c] += amplitude * kernel


def splat_many(image: np.ndarray, us, vs, amplitudes, sigma: float) -> None:
    """Vectorised convenience wrapper for a field of point sources."""
    for u, v, a in zip(np.atleast_1d(us), np.atleast_1d(vs), np.atleast_1d(amplitudes)):
        splat_gaussian(image, float(u), float(v), float(a), sigma)


def splat_square(image: np.ndarray, u: float, v: float, amplitude: float,
                 side_px: float, sigma: float) -> None:
    """
    Add one *resolved* square target, blurred by the PSF, in place.

    PS26169 specifies the benchmark target as a square of configurable
    side (10 px by default), not as a point. That is not cosmetic. A
    point source puts nearly all its flux in one pixel, so peak-pixel
    thresholding works and centroiding is trivially accurate. Spread the
    same flux over a 10x10 square and the peak falls by roughly two
    orders of magnitude while the total is unchanged -- a detector tuned
    on peak brightness stops seeing the target entirely, and one that
    integrates keeps working. Rendering the spec's actual shape is what
    makes that difference measurable rather than arguable.

    The profile is a box convolved with the Gaussian PSF, which is
    separable and has a closed form: the convolution of a uniform box of
    width ``s`` with ``N(0, sigma^2)`` is the difference of two normal
    CDFs. Evaluated on the pixel grid and then normalised to unit sum,
    so ``amplitude`` is total signal and photometry stays consistent
    with ``splat_gaussian`` -- the same beacon must not change
    brightness merely because it was given a size.
    """
    if amplitude <= 0.0 or sigma <= 0.0:
        return
    if side_px <= 0.0:
        splat_gaussian(image, u, v, amplitude, sigma)
        return

    height, width = image.shape
    half = side_px / 2.0
    radius = int(np.ceil(half + 4.0 * sigma))
    u0c, u1c = max(int(np.floor(u)) - radius, 0), min(int(np.floor(u)) + radius + 1, width)
    v0c, v1c = max(int(np.floor(v)) - radius, 0), min(int(np.floor(v)) + radius + 1, height)
    if u0c >= u1c or v0c >= v1c:
        return

    root2 = np.float32(np.sqrt(2.0))

    def _profile(coords, centre):
        d = coords + np.float32(0.5) - np.float32(centre)
        # 0.5*(erf(a) - erf(b)) is the box-Gaussian convolution; erf comes
        # from math via the vectorised identity below so that numpy alone
        # is enough and scipy stays out of the dependency list.
        hi = (d + np.float32(half)) / (np.float32(sigma) * root2)
        lo = (d - np.float32(half)) / (np.float32(sigma) * root2)
        return 0.5 * (_erf(hi) - _erf(lo))

    xs = np.arange(u0c, u1c, dtype=np.float32)
    ys = np.arange(v0c, v1c, dtype=np.float32)
    kernel = np.outer(_profile(ys, v), _profile(xs, u))
    total = kernel.sum()
    if total <= 0.0:
        return
    image[v0c:v1c, u0c:u1c] += amplitude * (kernel / total)


def _erf(x: np.ndarray) -> np.ndarray:
    """
    Abramowitz & Stegun 7.1.26, vectorised.

    Maximum absolute error 1.5e-7, which is four orders of magnitude
    below the shot noise on any pixel this is used to fill -- and it
    avoids adding scipy to a dependency list that a judge has to install.
    """
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    sign = np.sign(x)
    ax = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-ax * ax)
    return sign * y
