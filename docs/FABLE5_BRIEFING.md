# Briefing for the parallel software session (Fable 5)

> ## ✅ COMPLETE — this briefing has been carried out
>
> The parallel account it addressed is no longer accessible, but its work
> was committed and merged: PRs #2–#5 on `main` (adaptive blink-frequency
> estimation, the temperature-calibrated verifier, the 24-condition
> benchmark, the live engine and the ZD-1 dashboard). Nothing was lost.
> Kept for the reasoning it records, not as an open instruction.

*Paste this as your first message in that session. It is also committed
here so it survives even if the paste is lost.*

---

You're working on **ZeroDrift**, Team SIH26169 (ISRO) — an AI-based
virtual camera tracking system for coarse alignment of mobile FSOC
(free-space optical communication) terminals. Another Claude session, on
another account, is working the same repo **in parallel** right now,
handling documentation, the pitch deck, and the physical hardware build.
Read this whole file before touching anything.

## Read this first, in order

1. **`docs/PROJECT_STATE.md`** — the canonical numbers table (with
   sources), current open threads, and the git rules for two accounts
   sharing one repo. If a number you're about to use isn't on that
   table, don't use it without checking `runs/mc-leo/summary.json` or
   `docs/technical_report.md` directly.
2. **`docs/WINNING_PLAN.md`** — the full competition strategy. Your work
   is **Tier 1.4** ("AI depth") plus general accuracy work — see below.

## Git rules — read before your first commit

- **Branch off `main`**, something like `git checkout -b accuracy-work`.
- **Never commit onto `claude/session-01f6edpdcuue3caljzzaz7fh-h9tr19`**
  — that's the other session's branch, mid-flight, currently 9+ commits
  ahead of `main` with no divergence. Touching it risks a collision.
- **Never force-push anything.** Not your branch, not `main`. This is
  the one action that can actually destroy the other session's work.
- When you're done, that's a normal PR — not a direct merge.
- **Update `docs/PROJECT_STATE.md`** when you finish something meaningful
  and commit it. That file is the handoff between sessions — if it's
  stale, whoever reads it next starts blind.

## What "improve the software's accuracy" means here, specifically

Not "make the numbers bigger." The existing numbers (1.27s acquisition,
97.6% median lock retention, 0/64 decoy locks) are real, measured, and
already strong — see `docs/PROJECT_STATE.md` §2 before changing anything
that would invalidate them. The actual opportunity, per
`docs/WINNING_PLAN.md` §3.4:

- **Adaptive blink-frequency estimation.** The tracker currently assumes
  a known 4.0 Hz beacon (see `tools/webcam_beacon_demo.py --blink`
  default). Infer the beacon's actual modulation frequency from the data
  instead of assuming it, then verify at the inferred rate.
- **Calibrated uncertainty on the AI verifier's output**, so the state
  machine can refuse a marginal lock instead of guessing.
- **Extend the classical-vs-NN benchmark** (currently AUC 0.957 vs 0.900
  on short windows, in `docs/defence_brief.md`) across window length,
  SNR, and frequency — and publish where the classical method wins, not
  just where the network does. That honesty is the house style — see
  `docs/defence_brief.md` for the tone to match.
- Multi-target simultaneous tracking (§3.5 in the plan) is a second,
  independent piece of work if you have bandwidth after the above.

## Physical hardware being built right now, in parallel — keep this compatible

Two units are being built alongside your software work. You don't need
to build or test them, but **your changes need to stay compatible with
what they'll eventually feed into the pipeline**:

### 1. The tracker rig (`docs/rig_mk2_build_guide.md`)
Camera + laser on a closed-loop pan-tilt stage. Talks to the Nano over
serial, 115200 baud:
```
P<int> T<int>   coarse pan/tilt target, in motor steps
p<int> t<int>   fine pan/tilt target, in servo degrees
L0 / L1         laser off / on
V0 / V1         vibration injector off / on
```
`src/fsoc_pat/hil/` (`rig.py`, `calibrate.py`, `live.py`) is the
existing scaffolding for driving real hardware through this interface —
if your accuracy work touches the tracking/control loop, check whether
`hil/` calls into it, so a future hardware run doesn't silently diverge
from the simulated path.

### 2. The beacon unit (`docs/beacon_build_guide.md`, new)
A dedicated Arduino-driven blinking LED — replaces "hold up a phone
strobe app" with a frequency-precise, adjustable target. Its own serial
protocol, own Nano, own battery:
```
F<float>   set blink frequency in Hz (boot default 4.0)
B<0-255>   set brightness (PWM)
M0 / M1    steady-on / blinking
```
**This is deliberately relevant to your adaptive-frequency-estimation
work above.** The beacon can be commanded to any frequency at build
time or live during a demo — which means once it exists, your frequency
estimator has a real, controllable, ground-truth-known signal to
validate against, not just simulated frequency sweeps. Worth keeping in
mind when you design the estimator's interface: a `expected_hz` that
defaults to 4.0 but can be overridden is what will make this pairing
work later.

There is also a **decoy unit** (steady, non-blinking, deliberately
brighter) — no firmware, exists purely so the beacon-vs-decoy
discrimination claim is demonstrable live, not just asserted.

## The one thing not to break

`0 / 64` decoy locks across the Monte Carlo campaign is a load-bearing
number in the pitch (`docs/technical_report.md`, `docs/defence_brief.md`,
the deck). If any accuracy change touches the identification gate, rerun
the campaign (`runs/mc-leo/`) and confirm that number still holds before
calling the change done — a regression there is worse than no
improvement at all.
