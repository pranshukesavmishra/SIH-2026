# PS26169 — specification compliance

*Last verified 19 Sept 2026 against the published "Parameters and
Specifications" table.*

This file exists because we spent months benchmarking against our own
scenarios and then read the evaluators' table properly. Three of their
numbers are stricter than ours, and one of our headline results was
obtained under conditions the rules do not permit. That is recorded here
rather than quietly corrected, because a judge who finds it themselves
will ask why we did not.

**The rule this file enforces:** every performance number we publish is
measured on `scenarios/ps26169_benchmark.yaml`, which encodes the
evaluators' parameters and nothing else. Our own scenarios stay, because
a real terminal tracking a LEO pass is the actual application — but they
are labelled as ours and their numbers are never quoted against the
spec's limits.

## Where our defaults differed from the spec

| Parameter | Spec | Our default was | Why it mattered |
|---|---|---|---|
| Camera FOV | 4° × 3° | 6° | A wider field finds the target sooner. Our acquisition times were measured on an easier problem. |
| Max pan/tilt speed | 5–10°/s, default 5 | 20°/s | **The serious one.** A mount four times faster closes on the target four times sooner. Every acquisition figure we had published was invalid against the spec. |
| Motion patterns | ≥ 4, **Figure-of-8 required** | 7 kinds, no figure-of-8 | Mandatory and absent. It is also the hardest of the four: elevation acceleration reverses sign four times per period, so a constant-velocity filter mispredicts at exactly the crossing point. |
| Noise | Salt & Pepper **around 10% of image**, Gaussian, Poisson | Gaussian + Poisson only | Salt & pepper is not a restatement of the other two. Gaussian and Poisson act on the collected charge and are bounded by it; salt lands at full scale regardless. **And the density matters: we first built for 0.1%, a hundredth of what the table asks.** At 10% the naive detector finds *nothing at all* — the impulses lift its noise estimate above the beacon. |
| Initial camera position | centre of screen | an offset guess | Trivial to get right, and it decides whether acquisition is a real search. |
| Platform motion | **mandatory, linear** | a 0.7 Hz oscillation | Not the same control problem. An oscillation is zero-mean over its period and can be filtered; a drift never is, and has to be nulled. |
| Tracking error | **≤ 10 pixels** | reported in µrad only | Both benchmark stages are scored on *centroiding error*, a pixel quantity, and 60% of the marks ride on them. A report in µrad alone leaves the evaluator converting our numbers against a threshold written in the other unit. |
| Target shape | Square, 10 × 10 px (range 5–20) | Unresolved point source | At equal total flux a 10 px square has ~8× lower peak pixel. A detector tuned on peak brightness sees a point source and misses the spec's target. |
| Atmospheric conditions | Clear / Haze / Fog / Rain / Low light | One brightness knob | The five are physically different: fog takes signal *and* adds background, rain barely attenuates but adds bright point-like transients, low light *improves* SNR for an active beacon while breaking any adaptive threshold. |
| Camera jitter | ±20 px/frame | ~1.3 px RMS | At 4° FOV one pixel is 109.1 µrad, so ±20 px is 2183 µrad — about eighteen times the disturbance we were injecting. |
| Platform motion | ±20 px/frame | not modelled separately | Distinct from jitter: low frequency and large excursion, where jitter is small and fast. Modelled as a 0.7 Hz mode. |

## Where we already complied

| Parameter | Spec | Ours |
|---|---|---|
| Camera resolution | 640 × 480 | 640 × 480 |
| Update rate | ≥ 20 FPS | 30 Hz simulated |
| Screen/target range | target 5–20 px | configurable, 10 px in the benchmark |
| MP4 input, bypassing the PTZ camera | required (Benchmark-2, 30%) | `fsoc_pat.hil.serve --video clip.mp4`, present and working |

## What the spec's conditions did to our tracker

Running `scenarios/ps26169_benchmark.yaml` for the first time, with every
spec parameter applied at once:

```
Acquisition time         not achieved
Lock retention           65.8 %
Beacon inside FOV         3.3 %
Mean detections/frame    23.7
Processing throughput    14.8 fps  (BELOW the 20 FPS floor)
```

A six-way ablation — removing one spec parameter at a time — named
salt-and-pepper noise as the sole cause. Field of view, slew rate,
target size and jitter each changed the result by nothing measurable;
without impulse noise, detections fell from 23.7 per frame to 4.7 and
acquisition completed in 3.0 s.

The detector had no impulse rejection. It now does (`PointDetector.
reject_impulse_noise`), and in the loop it works exactly as designed:

```
Mean detections/frame     4.7   (was 23.7; matches the clean-frame figure)
Acquisition time         4.33 s (was: never achieved)
```

**That is progress, not compliance.** A second and independent failure
remains, and it is not caused by the impulse noise — it was visible in
the `no_saltpepper` ablation too:

```
Acquisition time         4.33 s   vs   <= 2 s required
Beacon inside FOV         8.3 %
Pointing error, mean    368 mrad  = 21 degrees
State occupancy         COAST 68.9%   TRACK 0.1%
Reacquisitions           454 in 120 s
Processing throughput   14.4 fps  vs   >= 20 FPS required
```

The mount runs 21 degrees away from a target whose whole path spans
1.4 degrees. The shape of it is legible in the state occupancy: the
beacon blinks at 4 Hz with a 50% duty cycle against a 30 fps camera, so
it is genuinely dark in most frames, the tracker spends 69% of its time
in COAST, and with jitter eighteen times larger than anything it was
tuned against, coasting accumulates error faster than the next detection
can correct it.

This is the same failure mode the live demo hit and was rewritten to
fix, and the rule that fixed it there applies here: **prediction steers
the search, measurement moves the boresight.** A coast must be bounded
and must never be written back as truth. That fix is the next piece of
work and it is not a tuning exercise.

Throughput is a second, separate problem: 14.4 fps against a 20 FPS
floor. Impulse rejection costs two median passes and two morphological
passes per frame, which is part of it.

## What this changes about the hardware build

Nothing is added to or removed from `docs/data/bom_tier_a.json`. The spec
describes a virtual camera viewing a simulated scene; our physical
terminal is a demonstration we chose to build, not something the problem
statement asks for. Two notes stand:

- **The 12 mm lens sees 22° × 16°, not 4° × 3°.** Correcting that
  optically needs roughly a 69 mm lens, which in M12 is expensive, dim,
  and would reduce the terminal to a 21 cm view at 3 m — fragile on
  stage for no marks. We keep the 12 mm lens and stop describing the rig
  as reproducing spec conditions. Rig tracking error is reported in
  **mrad as well as pixels**, because pixels are not comparable between
  two systems with different °/px.
- **The vibration motor is the one BOM line the spec actively
  justifies.** ±20 px/frame of camera jitter is a requirement, not a
  flourish; at the rig's 0.0172°/px that is 0.34° of shake, which a 3 V
  motor delivers easily.
