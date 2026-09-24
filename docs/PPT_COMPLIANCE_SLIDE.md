# The compliance slide — what to put on it, and where

**Short answer to "do we mention the PS data on the last page, in
research?"** No. Not as the PS text, and not on the references page.

Two reasons, both about how marks are actually awarded.

1. **The references page is for citations** — ITU-R P.1621, CCSDS optical
   comms, LCRD/TBIRD, the papers we actually leaned on. The problem
   statement is not research; it is the requirement. Putting a
   requirement among citations reads as padding.
2. **Restating the PS earns nothing.** The evaluators wrote it. Every
   team's deck opens by restating it, which is precisely why it does not
   distinguish anyone.

**What does earn marks** is a compliance table: their parameter, our
value, tick. Technical Evaluation is 20% and its *first* listed
criterion is "Understanding of the problem". A table proving we read
every row of their spec and built to it demonstrates that in one glance;
a paraphrase of their background paragraph does not.

## Where it goes

Not last. Put it as the **slide before the closing/impact slide** —
while the evaluators are still in technical mode, right after the
architecture and results. The closing slide stays the closing slide.

## What goes on it

One table, twelve rows at most, three columns: **Parameter · Spec ·
ZeroDrift**. Use their row names verbatim so it maps one-to-one to the
table in front of them.

| Parameter | Spec | ZeroDrift |
|---|---|---|
| Camera resolution | 640 × 480 | 640 × 480 |
| Camera FOV | 4° × 3° default | 4° × 3° |
| Camera update rate | ≥ 30 Hz | 30 Hz |
| Max pan / tilt speed | 5–10°/s, default 5 | 5°/s |
| Target shape / size | square, 10 × 10 px | square, 10 × 10 px |
| Motion patterns | ≥ 4 incl. Figure-of-8 | 7, incl. Figure-of-8 |
| Image noise | Salt & Pepper ~10%, Gaussian, Poisson | all three, S&P at 10% |
| Camera jitter | ± 20 px/frame | 19.8 px p99, measured |
| Platform motion | ± 20 px/frame, linear | linear drift, 6 px/frame |
| Atmosphere | Clear/Haze/Fog/Rain/Low light | all five, `--atmosphere` |
| Processing speed | ≥ 20 FPS | *(fill from the current run)* |
| Tracking error | ≤ 10 px | *(fill from the current run)* |
| Acquisition / re-acquisition | ≤ 2 s / ≤ 1 s | *(fill from the current run)* |

**Leave the last three blank until they are true.** A compliance table
with a number we cannot reproduce on demand is worse than no table: the
Q&A is 20% of the Technical Evaluation and that is exactly the row an
evaluator will ask you to run.

## The line to say out loud

The one worth saying, because almost nobody will have done it:

> "Their 2000-pixel screen, at the camera's own 0.00625° per pixel, is
> 12.5°. From the centre the furthest corner is 8.84°. A 5°/s mount
> covers that in 1.77 seconds — and their acquisition limit is 2
> seconds. The specification is a closed system, so we benchmark inside
> it rather than on scenarios of our own choosing."

That is thirty seconds, it is checkable arithmetic, and it demonstrates
"understanding of the problem" better than any paragraph.

## What NOT to put on the deck

- The PS background paragraphs, reworded.
- The evaluation-criteria table. They wrote it; showing it back reads as
  telling them their job.
- Any row we have not measured under
  `scenarios/ps26169_benchmark.yaml`.
