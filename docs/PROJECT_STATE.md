# ZeroDrift — Project State

**The portable memory.** Any new session, on any account, in any model:
clone this repo and read this file first. It is the authority on what is
done, what is open, and which number is the real one.

Last updated: 2026-09-18 (rev 5 — session branch merged with main: accuracy
work, Mk2 live software and the Mk3 physical design now in one history)

---
## 1. Identity

| | |
|---|---|
| Team | **ZeroDrift** — Jabalpur Engineering College |
| Problem Statement | **SIH26169**, set by **ISRO** (Dept. of Space) |
| Title | AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals |
| Theme / Category | Smart Automation / **Software**
- [x] ~~`hil/` could not drive either firmware~~ — **found and fixed 18 Sept.**
  Three layers written across three weeks each assumed a different wire
  format: `hil/rig.py` sent degrees, the Mk2 firmware parsed motor steps
  (a silent 4.4× error), the status query `?` did not exist so the host
  spun its whole timeout and reported the gimbal had never moved, and
  `rig_track.py` sent laser commands with no newline, which ate the next
  pointing command. All fixed, one spec in `docs/HARDWARE_PROTOCOL.md`,
  and `check_protocol()` now catches a mismatch at startup. This was our
  own drift, not the parallel account's — those files predate it. |
| Repo | `github.com/pranshukesavmishra/SIH-2026` |
| Live replay console | `zerodrift-fsoc-pat.netlify.app` |
| Status | 2nd Runner-Up, institute internal round (11 Sept 2026) |

**Team (6, locked — changing members disqualifies the nomination):**
Aryan Singh (leader, CSE 3rd yr) · Pranshu Mishra (Mechatronics 3rd) ·
Aashna Verma (IPE 2nd) · Palak Uikey (ECE 2nd) · Vivek Rajput (IT 3rd) ·
Shivanand Sahu (IT 3rd).

---
## 2. Canonical numbers — check here before writing any number anywhere

Deck, report, pitch and chat must all agree with this table. A number
not on this list, or not traceable to its source, does not go in front
of a judge.

| Value | What it actually means | Source of truth |
|---|---|---|
| **1.27 s** | Median acquisition time | `runs/mc-leo/summary.json` → `acquisition_time_s.p50` |
| **2.77 s** | p95 acquisition | same → `.p95` |
| **4.0 s** | Worst-case acquisition | same → `.max` |
| **100%** | Acquisition probability, all runs | same → `acquisition_probability` |
| **97.5%** | Lock retention, **campaign median** | same → `lock_retention_pct.p50` |
| **94.5%** | Lock retention p5 | same → `.p5` |
| **91.6%** | Lock retention, **campaign worst** | same → `.min` |
| **98.3%** | Lock retention, **featured demo run only** | `docs/media/telemetry_run.json` |
| **768 µrad** | Median of p95 pointing error | same → `pointing_error_p95_urad.p50` |
| **198 µrad** | Median pointing error, demo run | replay console / demo run |
| **0 / 64** | Runs with any decoy lock | same → `runs_with_any_decoy_lock` |
| **99.3%** | Link closure **with modelled fine stage** | `docs/technical_report.md` L281–283 |
| **14.7%** | Link closure, **coarse stage alone** | `docs/technical_report.md` L281 |
| **3.1 dB** | Mean link margin | `docs/technical_report.md` L283 |
| **AUC 0.957 vs 0.900** | NN verifier vs classical, short window | `docs/defence_brief.md` |
| **132 / 132** | Automated tests passing (+1 skipped) | CI, verified 18 Sept post-merge |
| **8–21 ms** | Tracker time per 33 ms frame, 2 cores | engine benchmark |
| **₹0.22** | Electricity, full 64-run campaign | `docs/economic_feasibility.md` |
| **207×** | Throughput vs hardware bench | `docs/economic_feasibility.md` |

> ⚠️ **The known trap:** 98.3% (demo-run lock retention) and 99.3%
> (link closure) get confused. They are different metrics. Fixed in the
> v3 deck (18 Sept): slide 5 now carries 99.3% with bars to scale.

---
## 3. Where things live

```
docs/
  technical_report.md      10–15pp deliverable — the numbers' origin
  economic_feasibility.md  cost arithmetic, all assumptions stated
  defence_brief.md         deep Q&A prep for judges
  pitch_script.md          3-min pitch + role split
  PROJECT_STATE.md         ← you are here
  WINNING_PLAN.md          full national-round strategy, tiered by effort/impact
  FABLE5_BRIEFING.md       briefing for the parallel software session
  TERMINAL_MK3.md          ← THE physical build. Supersedes Mk1 and Mk2.
  HARDWARE_PROTOCOL.md     wire format, v3 — firmware and host both obey it
  rig_build_guide.md       Mk1 (built, both servos dead) — historical
  rig_mk2_build_guide.md   Mk2 spec — superseded by Mk3, kept for the encoder notes
  beacon_build_guide.md    Beacon + decoy units — the target, not the tracker
  PHYSICAL_BOM_MASTER.md   Mk2-era parts list — superseded by TERMINAL_MK3.md §2
  zero_cost_demo.md        ₹0 webcam fallback demo
  user_manual.md           deliverable
  submission/              the deck PDF
  media/                   telemetry, panels, assets
src/fsoc_pat/              the engine (detector, tracker, control, ai, gui)
  resources.py             resolves shipped data; frozen-build-safe
  hil/engine.py            the REAL tracker on live frames
  hil/mk2.py               Mk2 protocol driver + safety envelope + dry-run
  hil/serve.py             engine + SSE telemetry + MJPEG + ZD-1 dashboard
  hil/rig_detect.py        lightweight low-dependency detector (live console)
  hil/boresight.py         dot-vs-beacon loop — cancels parallax, Mk3
tools/rig/                 firmware + tracker + accuracy logger
runs/mc-leo/summary.json   the 64-run campaign — source of most numbers
packaging/                 build scripts + fsoc-pat.spec (cv2-Qt conflict fixed)
```

---
## 4. Open threads

**Submission (hard deadline 30 Sept 2026)**
- [ ] Rename consent letter to `ZeroDrift_Consentletter.docx`, upload to the Google Form
- [ ] Idea submission on the SIH portal — **first-come-first-served, 500 ideas per PS**, do not wait for the deadline
- [ ] Team ID still blank on deck slide 1

**Deck fixes — ALL DONE in v3 (18 Sept, `docs/submission/ZeroDrift_SIH26169.pptx/pdf`,
rebuilt from the official template + the team's 10-Sept graphics; source +
assets: `docs/submission/deck_src/` — `python build_deck_v3.py` regenerates it)**
- [x] Slide 5: 98.3% → 99.3% (matches the technical report), bars drawn to scale
- [x] Slide 2: 98.3% chip relabelled "lock held · featured demo run"; 1.27 s chip
      relabelled "median acquisition · 64 runs" (also fixes the "Acquistion" typo)
- [x] Slide 2: page number correct (2)
- [x] Economic feasibility panel on slide 5 (capital-cost card + ₹0.22 / 207× / ₹15 cr)
- [x] Slides 1 & 2 lead with the problem in one line
- [ ] Team ID still blank on slide 1 — fill when SIH portal issues it

**Software**
- [x] ~~`hil/` could not drive either firmware~~ — **this was a stale-branch
  artefact, not a live bug.** The mismatch was real in this session's working
  tree, but `main` had already fixed it on **10 Sept** (`05005b7`), eight days
  before it was "found" here; this branch was 42 commits behind and reading an
  old snapshot. Recorded because the wrong version of this claim was stated
  confidently to the team and is worth not repeating: check the merge-base
  before reporting a bug in shared code.
- [x] `packaging/fsoc-pat.spec` committed (root cause: `.gitignore`'s `*.spec` was
      hiding it — negated now). Both build scripts and CI use the spec; it bundles
      `scenarios/` + `models/`, strips cv2's bundled Qt (which otherwise shadows
      PySide6's platform plugins and kills the GUI on launch). Verified on Linux:
      headless report runs, GUI event loop starts offscreen.
- [x] Accuracy work landed on branch `accuracy-work` (PR #3, 18 Sept): adaptive
      blink-frequency estimation (measured ±0.1 Hz, blind mode when no frequency
      is agreed, pairs with the beacon unit's `F<hz>` command), "measured blink"
      row in the ZD-1 console, temperature-calibrated verifier with a
      validation-derived abstain band (vote stays raw-scale — see the commit
      for the measured regression that forced that), and a 24-condition
      classical-vs-NN benchmark in `docs/benchmark_identification.md`
      including the 21 cells the classical method wins. 102/102 tests; the
      64-run campaign guard re-ran on the final code: **0/64 decoy locks
      confirmed**. Canonical decimals above refreshed from that rerun; the
      p50 1.27 s, max 4.0 s, min 91.6 % and 0/64 are unchanged.

**Mk2 live software — DONE (18 Sept, `mk2-live-software` branch)**
- [x] The REAL engine on real camera frames: `hil/engine.py` runs
      `CoarseAlignmentTracker` (CFAR, blink gate + adaptive frequency, IMM,
      Smith predictor, AI verifier) on live/video/array frames — the
      "identical code drives real optics" claim is now true by construction.
- [x] `hil/mk2.py`: v2-protocol driver (P/T steps, p/t servo degrees, L, V)
      with software safety envelope + dry-run mode. `hil/serve.py`: one
      process = engine + SSE telemetry + MJPEG + dashboard; `docs/rig.html`
      is the live ZD-1 console (truth-referenced tiles deliberately absent —
      no ground truth exists off-simulation). `tools/rig/beacon_firmware.ino`
      implements the F/B/M beacon protocol. Run guide: `docs/rig_live.md`.
- [x] Verified end-to-end with a synthetic beacon video: TRACK lock on the
      blinking source (brighter steady lamp refused), measured blink 3.0 Hz,
      8–10 ms/frame. 7 new tests; suite green.
- [ ] On real hardware still to do: measure FOV + plate scale
      (`hil.calibrate`), verify stepper direction signs, then
      `python -m fsoc_pat.hil.serve --port-serial auto`.

**Browser live demo (live.html) — motion-hardened (18 Sept, `live-tracker-v2`)**
- [x] Fast-moving beacon stays locked: velocity learned from measured position
      deltas (true target velocity, dark phases included), feed-forward
      prediction scaled by the real inter-frame gap, speed/blind-time-grown
      search disc + ROI + tether, ROI-wide recapture once blind past a normal
      dark phase, lag-corrected + overshoot-capped map re-tether. All bounded
      by the modulation map's 3x drop budget, so identity still rules.
- [x] Honest COASTING state (amber, dashed ring) whenever the lock is carried
      by prediction — no more green LOCKED with blink 0.00 on a stale ring.
- [x] MARGIN vs NOISE floored (max ~50x; the six-digit readout is gone).
- [x] RIG CAMERA VIEW button: probes localhost:8765, opens the full-engine
      rig console (hil/serve.py) when running, explains how to start it when not.
- [x] Verified end-to-end in headless Chromium with a synthetic camera
      (`tools/web/test_live_motion.mjs` + `fake_cam.js`): 5/6 runs fully clean,
      worst case = temporary lag with honest COASTING and recovery; zero lock
      losses, zero decoy captures across all runs.

**Physical terminal — Mk3 (`docs/TERMINAL_MK3.md` is the authority)**

Architecture decided 18 Sept: a self-contained scanning terminal, not a
table demo. Camera rides on the gimbal boresighted with the laser; the
Pi runs the pipeline on-board; the Nano does motion only.

- [x] ~~Servos~~ — **removed from the design entirely.** Mk1 stripped two.
  A hobby servo's backlash (~17 mrad) exceeds the error this rig measures.
  Resolution comes from microstepping instead: Tier A is 1.96 mrad/step
  with the AS5600 measuring to 1.53 mrad, and nothing to shear.
- [x] Parallax problem solved without modelling it — beacon 4 Hz, laser
  7 Hz, loop closes on the dot-to-beacon pixel error. `hil/boresight.py`,
  14 tests passing.
- [x] Re-budgeted to a student build: **Tier A, ₹6,124**, in
  TERMINAL_MK3.md §2. Nothing load-bearing was cut — the dot-closed loop
  and modulation-identity are software and cost ₹0; the encoders are
  ₹697 and stay. What was cut is margin: Pi 5, global shutter, TMC2209,
  0.9° motors, belt reduction, true bandpass filter. Laptop runs the
  pipeline; the camera still rides on the gimbal.
- [ ] Order parts — TERMINAL_MK3.md §2 Tier A. **Two order-time traps:**
  magnets must be **diametric** not axial, and buy the 100 µF caps for
  VMOT or the first power-up kills both drivers. Also set the A4988 Vref
  before attaching a motor.
- [ ] Prices: ✅ verified are NEMA17 ₹749, A4988 ₹170, AS5600 ₹249,
  TCA9548A ₹199, PSU ₹279, acrylic+brackets ₹450. The rest are estimates
  — price-check before ordering, and say which is which if a judge asks.
- [ ] **If budget ever allows one upgrade, buy the GT2 3:1 belt (+₹1,740).**
  1.96 → 0.65 mrad/step, and it divides the motor's own error by three,
  which microstepping cannot do. Everything else in Tier B is comfort.
- [ ] Build per §3, stage by stage. Do not pass a stage that fails its check.
- [ ] Beacon needs rebuilding at 650 nm to match the camera's bandpass filter

**Outreach**
- [ ] DRDO chairman brief — message drafted, send status unknown

**Verification pass — 18 Sept, post-merge**

Everything below was checked against its source, not restated:

- [x] All 9 campaign numbers re-derived from `runs/mc-leo/summary.json`; all
      match the table above to the stated precision. 7 doc-sourced claims
      (99.3 / 14.7 / 3.1 dB / AUC 0.957 vs 0.900 / ₹0.22 / 207×) confirmed
      present at their cited files.
- [x] Every remote branch is contained in this one; nothing unmerged, nothing
      unpushed. Fable 5's work is fully present via PRs #2–#5.
- [x] Every file path referenced in `docs/*.md` exists.
- [x] **Fixed: the parts list disagreed with itself.** `TERMINAL_MK3.md` §2
      summed to ₹5,944 while claiming ₹6,124, and the printed guide said
      ₹6,331. The missing row was the diametric magnets — the one part whose
      absence stops the build. There is now a single source
      (`docs/data/bom_tier_a.json`), the markdown table is generated from it,
      and `tests/test_bom_consistency.py` fails if the JSON, the markdown and
      the PDF disagree, if a build-stopping part is dropped, or if the deleted
      servos reappear. Verified by mutation.
- [x] **Fixed: `83 / 83` tests was stale** — 132 passing.
- [x] **Fixed: four superseded docs carried no warning.** `PHYSICAL_BOM_MASTER.md`
      in particular still listed the MG90S servos and omitted the magnets and
      capacitors; anyone buying from it would repeat the exact mistake. All four
      now carry a header.

**Known gaps — open, not fixed**

- [ ] **`docs/technical_report.md` is ~2,491 words ≈ 5 pages. PS26169 requires
      10–15.** This is a submission deliverable and the largest outstanding
      risk on the list.
- [ ] `docs/user_manual.md` is ~957 words ≈ 2 pages; thin for a deliverable.
- [ ] `src/fsoc_pat/hil/boresight.py` is tested (14 tests) but **wired to
      nothing** — it targets Mk3 hardware that does not exist yet. Legitimate,
      but it is not currently proving anything at runtime, and `main`'s
      self-laser rejection in `docs/live.html` is the better mechanism to fold
      into it (a matched filter against the recorded laser command history,
      rather than assuming a fixed 7 Hz).
- [ ] The frozen build still has not been run and launched on real Windows.

---
## 5. Git topology — how not to clobber anything

```
origin/main ──────●  (team's PowerPoint + site work)
                   \
                    ●──●──●──●──●──●──●──●──●──●──●──●  claude/session-01f6…h9tr19
                    |                        (docs, deck rebuilds, rig specs,
                    |                         economic feasibility, build fix,
                    |                         beacon/decoy units)
                    \
                     ●···  (Fable 5's branch, name unknown to this session —
                            it should be something like accuracy-work,
                            created fresh off main, per docs/FABLE5_BRIEFING.md)
```

- The session branch **contains everything on main** — no divergence, a
  clean fast-forward. Merging is safe whenever you want it.
- Nothing is lost if a session dies: everything is pushed.

### Working from a second account / a different model, safely

1. **Clone, don't guess.** `git clone` the repo and read this file.
2. **Branch first.** `git checkout -b <something-descriptive>` off `main`
   or off the session branch. Never commit straight onto someone else's
   branch.
3. **Never force-push** a branch you did not create. Never
   `git push --force` to `main`.
4. **Merge through a PR**, so both sides can see the diff before it lands.
5. **Update this file** when you finish something, and commit it. This
   file is the handoff — if it is stale, the next session starts blind.

Two sessions on two accounts can work at the same time without conflict
as long as each stays on its own branch and touches different files.
Same file, two branches → resolve at merge, never by force-push.
