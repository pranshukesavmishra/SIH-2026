"""
Turning a 12-bit sensor frame into an 8-bit image a person can read.

This lives in its own module because it was previously written twice --
once in the Qt view, once in the video exporter -- and both copies had
the same defect. Anything that renders a frame for human eyes imports
from here, so there is one transform to get right.

The defect, for the record: both divided by the frame maximum. That is a
per-frame auto-stretch, and on this data it is close to useless. The sky
background sits around 381 DN against a robust noise sigma of 10 DN, so
dividing by a 2183 DN beacon peak mapped the sky to mid-grey and left the
faint sources indistinguishable from noise. A single hot pixel set the
scale for the entire frame.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

#: Black point, in robust sigmas above the sky median. At 1.5 sigma about
#: 94% of sky pixels clamp to true black, so noise stops competing with
#: sources for the viewer's attention.
BLACK_SIGMAS = 1.5

#: White point, in robust sigmas above the sky median.
#:
#: Chosen so the beacon does NOT clip. On the baseline scenario the
#: beacon peaks 173 sigma above sky, so a white point below that pins it
#: at 255 and its brightness variation becomes invisible -- and the blink
#: is the entire thesis of this system. A display that hides the
#: modulation is the wrong display, whatever else it gets right.
#:
#: At 200 the beacon renders around 242/255 with headroom to vary, a
#: faint 10-sigma star still reaches 33/255 because the asinh curve
#: lifts the low end, and the sky stays at 0. Raising it further buys
#: nothing and costs faint-source visibility.
WHITE_SIGMAS = 200.0

#: asinh strength. Linear near the background, compressive above it.
#:
#: This is the knob that trades low-end lift against top-end headroom,
#: and it has to be read together with WHITE_SIGMAS. With white set high
#: enough that the beacon cannot clip, the usable range is wide, and a
#: weak curve leaves the faint stars at 33/255 -- technically visible,
#: invisible in a demo hall. At 90 a 5-sigma source reaches 60/255 and a
#: 10-sigma one 101/255, while the beacon still lands at 247 with room
#: to vary. Measured, not guessed.
ASINH_A = 90.0


def stretch_points(img: np.ndarray) -> Tuple[float, float]:
    """
    Black and white points for one frame, in DN.

    Both are referenced to the noise rather than to percentiles of the
    whole frame. A percentile black point lands *inside* the noise
    distribution: half the noise pixels sit above it and get stretched
    up into a salt-and-pepper field, which looks worse than the
    washed-out version it replaced.

    Sigma comes from the median absolute deviation, not the standard
    deviation, because a frame containing bright sources has a standard
    deviation dominated by those sources.
    """
    x = img.astype(np.float32)
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    sigma = max(1.4826 * mad, 1e-3)
    lo = med + BLACK_SIGMAS * sigma
    hi = med + WHITE_SIGMAS * sigma
    if hi - lo < 1.0:
        hi = lo + 1.0
    return lo, hi


def to_display(img: np.ndarray,
               points: Optional[Tuple[float, float]] = None) -> np.ndarray:
    """
    8-bit view of a sensor frame.

    Pass `points` to hold the stretch fixed across frames -- a stretch
    recomputed per frame breathes, and breathing hides exactly the
    brightness variation (scintillation, blink) that this system
    identifies targets by.
    """
    lo, hi = points if points is not None else stretch_points(img)
    x = img.astype(np.float32)
    y = np.clip((x - lo) / max(hi - lo, 1.0), 0.0, 1.0)
    y = np.arcsinh(y * ASINH_A) / float(np.arcsinh(ASINH_A))
    return (y * 255.0).astype(np.uint8)


def smooth_points(previous: Optional[Tuple[float, float]],
                  current: Tuple[float, float],
                  k: float = 0.12) -> Tuple[float, float]:
    """
    Exponential smoothing of the stretch, for live views.

    Adapts to a genuine scene change over roughly a second, without
    chasing a single bright frame.
    """
    if previous is None:
        return current
    return (previous[0] + k * (current[0] - previous[0]),
            previous[1] + k * (current[1] - previous[1]))
