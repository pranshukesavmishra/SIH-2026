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
| Noise | Salt & Pepper, Gaussian, Poisson | Gaussian + Poisson only | Salt & pepper is not a restatement of the other two. Gaussian and Poisson act on the collected charge and are bounded by it; salt lands at full scale regardless, which is what a peak-finding detector mistakes for a beacon. |
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
Processing throughput    14.8 fps  (BELOW the 20 FPS floor)
```

This is a failure, not a near miss, and it is the honest starting point.
The ablation that follows identifies which parameter is responsible;
fixing it is tracked in `docs/PROJECT_STATE.md`.

## Open items

- [ ] Processing throughput 14.8 fps against a ≥20 FPS floor.
- [ ] Acquisition under spec conditions.
- [ ] Re-run the Monte Carlo campaign on the benchmark scenario and
      republish every number that currently comes from our own scenarios.

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
