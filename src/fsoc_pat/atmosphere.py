"""
The five atmospheric conditions the problem statement names.

PS26169 lists "Clear / Haze / Fog / Rain / Low light" as a benchmark axis
but does not define them numerically, so this module does: each preset is
a small, explicit set of overrides applied to an existing scenario, and
the physical reason for every number is stated next to it. A judge can
disagree with a value; they cannot mistake what we simulated for what we
claimed.

Three distinct mechanisms are in play, and lumping them together is the
usual mistake:

  * **Extinction** removes beacon photons. Multiplicative on
    ``amplitude_e_s``, so it lowers signal without touching background.
  * **Scattering** adds background. Forward-scattered sunlight raises the
    sky level, which raises shot noise as its square root -- so fog hurts
    twice, once by taking signal and once by adding noise on top of it.
  * **Blur and scintillation** spread the beacon over more pixels and
    modulate it in time. This is the one that breaks a detector tuned on
    peak pixel value rather than on integrated flux.

Rain is the case that catches people out: its extinction is mild
compared with fog, but drops crossing the aperture produce brief,
bright, *point-like* events. Those look far more like a beacon than fog
ever does, which is why rain is a discrimination test and fog is a
sensitivity test.

Usage::

    cfg = SimConfig.load("scenarios/ps26169_benchmark.yaml")
    cfg = apply(cfg, "fog")
"""
from __future__ import annotations

import copy
from typing import Dict

# Each entry: beacon transmission, sky multiplier, added blur (px), added
# scintillation index, added tilt RMS (urad), clutter multiplier.
PRESETS: Dict[str, Dict[str, float]] = {
    "clear": {
        # Reference condition: the scenario as authored, untouched.
        "transmission": 1.00, "sky_gain": 1.00, "blur_px": 0.0,
        "scintillation": 0.00, "tilt_urad": 0.0, "clutter_gain": 1.0,
    },
    "haze": {
        # ~5 km visibility. Aerosol extinction is a couple of dB over a
        # short horizontal path; the sky brightens more than the beacon
        # dims, because the same aerosol that attenuates also scatters
        # sunlight into the aperture.
        "transmission": 0.65, "sky_gain": 1.8, "blur_px": 0.4,
        "scintillation": 0.05, "tilt_urad": 20.0, "clutter_gain": 1.0,
    },
    "fog": {
        # ~200 m visibility: the hardest sensitivity case. Extinction is
        # severe and the scattered halo raises the background by nearly an
        # order of magnitude, so SNR falls far faster than transmission
        # alone suggests. Droplet scattering also spreads the beacon into
        # a visible disc -- hence the largest blur term here.
        "transmission": 0.12, "sky_gain": 6.0, "blur_px": 2.2,
        "scintillation": 0.10, "tilt_urad": 30.0, "clutter_gain": 0.6,
    },
    "rain": {
        # Moderate rain. Extinction is modest -- water in drops blocks
        # much less path than the same water as fog droplets -- but drops
        # crossing the field make bright transient points, so clutter goes
        # up rather than down. This is the discrimination case: the blink
        # gate, not the SNR margin, is what survives it.
        "transmission": 0.55, "sky_gain": 1.4, "blur_px": 0.6,
        "scintillation": 0.18, "tilt_urad": 60.0, "clutter_gain": 2.2,
    },
    "low_light": {
        # Dusk. The beacon is unchanged -- it is a source, not a reflector,
        # which is the whole argument for an active beacon -- while the
        # sky falls by ~20x. Signal-to-noise therefore *improves*; what
        # degrades instead is everything the scene offers for context, and
        # a detector that adapted its threshold to a bright background
        # will now trigger on read noise. Included because a benchmark
        # that only ever gets harder never finds that failure.
        "transmission": 1.00, "sky_gain": 0.05, "blur_px": 0.0,
        "scintillation": 0.00, "tilt_urad": 0.0, "clutter_gain": 0.8,
    },
}


def apply(cfg, condition: str):
    """
    Return a copy of ``cfg`` with the named condition applied.

    The original is not modified, so a campaign can sweep all five
    conditions from one loaded scenario without them contaminating each
    other -- which is the bug this returning-a-copy exists to prevent.
    """
    key = condition.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in PRESETS:
        raise ValueError(f"unknown atmospheric condition {condition!r}; "
                         f"expected one of {sorted(PRESETS)}")
    p = PRESETS[key]
    out = copy.deepcopy(cfg)

    for beacon in out.beacons:
        # Extinction applies to every emitter in the scene, decoys
        # included: a decoy that stayed bright while the beacon faded
        # would make discrimination look easier in fog than in clear air,
        # which is backwards.
        beacon.amplitude_e_s *= p["transmission"]

    out.scene.sky_brightness_e_s *= p["sky_gain"]
    out.scene.terrain_brightness_e_s *= p["sky_gain"]
    out.scene.clutter_count = int(round(out.scene.clutter_count * p["clutter_gain"]))

    out.turbulence.enabled = True
    # Blur adds in quadrature because the two are independent Gaussians;
    # adding the sigmas linearly would overstate fog by about 40%.
    out.turbulence.seeing_blur_px = float(
        (out.turbulence.seeing_blur_px ** 2 + p["blur_px"] ** 2) ** 0.5)
    out.turbulence.scintillation_index += p["scintillation"]
    out.turbulence.tilt_rms_urad = float(
        (out.turbulence.tilt_rms_urad ** 2 + p["tilt_urad"] ** 2) ** 0.5)

    suffix = f" [{key}]"
    if not out.name.endswith(suffix):
        out.name += suffix
    return out
