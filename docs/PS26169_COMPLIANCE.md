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

## Where we already complied

| Parameter | Spec | Ours |
|---|---|---|
| Camera resolution | 640 × 480 | 640 × 480 |
| Update rate | ≥ 20 FPS | 30 Hz simulated |
| Screen/target range | target 5–20 px | configurable, 10 px in the benchmark |
| MP4 input, bypassing the PTZ camera | required (Benchmark-2, 30%) | `fsoc_pat.hil.serve --video clip.mp4`, present and working |

## The spec's numbers check out against each other

The whole benchmark rests on reading the table correctly, and three
independent rows agree:

- Screen is 2000 × 2000 px (row 1), and the camera resolves 4° across
  640 px (rows 3–4), so at the camera's own 0.00625°/px the screen spans
  **12.5° × 12.5°**.
- From the centre — where the camera starts, row 6 — the furthest corner
  is **8.84°** away.
- A 5°/s mount (rows 13–14) covers that in **1.77 s**, just inside the
  **≤ 2 s** acquisition limit (row 16).

That also settles what "Initial Target Location: Random" must mean. A
4°×3° window cannot *search* a 12.5° screen in 2 s — covering it takes
about ten tiles, each needing a slew plus a dwell long enough to catch a
beacon that is dark half the time. Measured: **48 s**. The 1.77 s figure
only works if the mount slews straight at the target, so the target must
be visible at t=0. `scenarios/ps26169_benchmark.yaml` starts it inside
the initial view; `scenarios/ps26169_cold_search.yaml` keeps the harder
reading available rather than quietly dropping it.

## What the spec's conditions did to our tracker

First run, every spec parameter at once:

```
Acquisition time         not achieved
Beacon inside FOV         3.3 %
Mean detections/frame    23.7
```

A six-way ablation named **salt-and-pepper noise** as the sole cause.
The detector had no impulse rejection; it now does, and at the spec's
10% density the naive detector finds *nothing at all* (the impulses lift
its noise estimate above the beacon) while ours finds the one correct
target. Detections per frame are back to 4.7, matching a clean frame.

## Diagnosis: what breaks it now

Four runs, 40 s each, one disturbance removed at a time.

| Run | Acquisition | Beacon in FOV | Lock retention | Pointing error (mean) |
|---|---|---|---|---|
| Full spec | 25.3 s | 60.4 % | 68.2 % | 53,646 µrad |
| Continuous beacon (no blink) | 2.63 s | 100 % | 36.1 % | 4,864 µrad |
| **No platform drift** (jitter kept) | **1.77 s** | **100 %** | 71.5 % | **1,026 µrad = 9.4 px** |
| No vibration at all | **1.80 s** | **100 %** | **97.5 %** | **362 µrad = 3.3 px** |

Read together, unambiguous:

- **±20 px/frame of structural jitter is already survivable.** With it
  and without the drift, acquisition is 1.77 s and pointing error 9.4 px
  — inside both the ≤2 s and ≤10 px limits.
- **The linear platform drift is the whole of what remains.** 6 px/frame
  — 30% of the permitted maximum — takes acquisition from 1.77 s to
  25.3 s.

The failure has a textbook signature, which is what makes it actionable.
A constant-velocity disturbance is a **ramp** in position. A loop with
proportional and derivative action has zero steady-state error to a step
and a **finite, constant** error to a ramp; only integral action drives
that to zero. Our controller has no integral term, so against a platform
moving at constant rate it settles at a fixed lag — and at this rate the
lag exceeds the field of view, which is why the beacon leaves the frame
and the tracker lives in COAST instead of TRACK.

That also says what *not* to do. Raising the proportional gain shrinks
the lag without removing it, and buys the reduction by making the loop
ring against the 20 px/frame jitter, which is the disturbance we can
already survive.

## Open items

- [ ] **Null the platform drift.** The ablation puts the whole remaining
      failure here. Needs integral action or explicit drift
      feed-forward — the IMM already carries a velocity state and the
      drift is observable in it — not tuning.
- [ ] **Bound the coast.** 72% of frames are COAST, because the beacon
      blinks at 4 Hz with a 50% duty cycle against a 30 fps camera.
      Prediction steers the search; measurement moves the boresight.
      This is the rule the live demo was rewritten around.
- [ ] **Processing throughput 9.2 fps** against a ≥20 FPS floor. Impulse
      rejection at 10% density iterates and costs two median plus two
      morphological passes per iteration.
- [ ] Re-run the Monte Carlo campaign on the benchmark scenario and
      republish every number that currently comes from our own
      scenarios.

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
