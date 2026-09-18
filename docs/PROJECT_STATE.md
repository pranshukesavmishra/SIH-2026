# ZeroDrift — Project State

**The portable memory.** Any new session, on any account, in any model:
clone this repo and read this file first. It is the authority on what is
done, what is open, and which number is the real one.

Last updated: 2026-09-18 (rev 2 — Tier 0.1 build fix + beacon/decoy units)

---
## 1. Identity

| | |
|---|---|
| Team | **ZeroDrift** — Jabalpur Engineering College |
| Problem Statement | **SIH26169**, set by **ISRO** (Dept. of Space) |
| Title | AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals |
| Theme / Category | Smart Automation / **Software** |
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
| **2.66 s** | p95 acquisition | same → `.p95` |
| **4.0 s** | Worst-case acquisition | same → `.max` |
| **100%** | Acquisition probability, all runs | same → `acquisition_probability` |
| **97.6%** | Lock retention, **campaign median** | same → `lock_retention_pct.p50` |
| **94.6%** | Lock retention p5 | same → `.p5` |
| **91.6%** | Lock retention, **campaign worst** | same → `.min` |
| **98.3%** | Lock retention, **featured demo run only** | `docs/media/telemetry_run.json` |
| **762 µrad** | Median of p95 pointing error | same → `pointing_error_p95_urad.p50` |
| **198 µrad** | Median pointing error, demo run | replay console / demo run |
| **0 / 64** | Runs with any decoy lock | same → `runs_with_any_decoy_lock` |
| **99.3%** | Link closure **with modelled fine stage** | `docs/technical_report.md` L281–283 |
| **14.7%** | Link closure, **coarse stage alone** | `docs/technical_report.md` L281 |
| **3.1 dB** | Mean link margin | `docs/technical_report.md` L283 |
| **AUC 0.957 vs 0.900** | NN verifier vs classical, short window | `docs/defence_brief.md` |
| **73 / 73** | Automated tests passing | CI |
| **8–21 ms** | Tracker time per 33 ms frame, 2 cores | engine benchmark |
| **₹0.22** | Electricity, full 64-run campaign | `docs/economic_feasibility.md` |
| **207×** | Throughput vs hardware bench | `docs/economic_feasibility.md` |

> ⚠️ **The known trap:** 98.3% (demo-run lock retention) and 99.3%
> (link closure) get confused. They are different metrics. The submitted
> deck currently has 98.3% on slide 5 where 99.3% belongs — see §4.

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
  rig_build_guide.md       Mk1 physical rig (built, tilt servo dead)
  rig_mk2_build_guide.md   Mk2 tracker spec — steppers + encoders
  beacon_build_guide.md    Beacon + decoy units — the target, not the tracker
  PHYSICAL_BOM_MASTER.md   combined real-priced parts list, tracker+beacon+decoy
  zero_cost_demo.md        ₹0 webcam fallback demo
  user_manual.md           deliverable
  submission/              the deck PDF
  media/                   telemetry, panels, assets
src/fsoc_pat/              the engine (detector, tracker, control, ai, gui)
  resources.py             resolves shipped data; frozen-build-safe (see §4)
tools/rig/
  rig_firmware_v2.ino      tracker firmware — steppers, fine servos, laser
  beacon_firmware.ino      beacon firmware — precise blink, serial-adjustable
  accuracy_logger.py       ground-truth measurement
runs/mc-leo/summary.json  the 64-run campaign — source of most numbers
packaging/                 build scripts + fsoc-pat.spec (now tracked — see §4)
```

---
## 4. Open threads

**Submission (hard deadline 30 Sept 2026)**
- [ ] Rename consent letter to `ZeroDrift_Consentletter.docx`, upload to the Google Form
- [ ] Idea submission on the SIH portal — **first-come-first-served, 500 ideas per PS**, do not wait for the deadline
- [ ] Team ID still blank on deck slide 1

**Deck fixes (content verified, edits pending in PowerPoint)**
- [ ] **Slide 5: 98.3% → 99.3%** (contradicts the technical report)
- [ ] Slide 2: label 98.3% as "featured demo run"
- [ ] Slide 2: page number reads "3", should be 2
- [ ] Slide 5: 14.7% bar not drawn to scale (~25% wide, should be ~15%)
- [ ] Insert economic feasibility panel (`docs/media/economic_feasibility_panel.png`)
- [ ] Slide 2: lead with the one-line problem, not the solution metaphor

**Software**
- [x] ~~`packaging/build.sh` references `packaging/fsoc-pat.spec` which does not exist~~ — **root cause found and fixed**: `.gitignore`'s stock `*.spec` rule was silently dropping the hand-maintained spec on every clone. Spec restored, tracked with an explicit `!` exception, and `src/fsoc_pat/resources.py` added so shipped data (AI weights, scenarios) resolves correctly inside a frozen bundle instead of via a `__file__.parents[2]` walk that escaped it. `tests/test_resources.py` passing (4/4).
- [ ] **Still outstanding**: actually run `packaging/build.bat` / `build.sh` on real Windows/Linux machines and launch the binary — unverifiable from a source checkout, could not be done in this session (no PySide6/PyInstaller/OpenCV here)
- [ ] Accuracy improvement work — now underway on the parallel Fable 5 account, see `docs/FABLE5_BRIEFING.md`

**Rig (no deadline — Grand Finale, Dec 2026 if selected)**
- [ ] Mk1 tilt servo dead (stripped gears); replacement also not moving — free-spin test never reported back
- [ ] Mk2 tracker: real-priced ₹4,190–4,410 (core) — see `docs/PHYSICAL_BOM_MASTER.md` for the verified breakdown, supersedes the older estimate in `rig_mk2_build_guide.md`'s own budget table
- [ ] Beacon + decoy units specced (`docs/beacon_build_guide.md`) — not yet built, not yet priced live (estimates only)
- [ ] Camera+laser combined head — diagram not yet drawn

**Outreach**
- [ ] DRDO chairman brief — message drafted, send status unknown

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
