# Demo video (v2) — how it is built

Order: intro → MK1 → [MK2 goes here] → Decoy test box → decoy run (Console, 85.6–95.6 s) → 8/8 test table → Live tracking box → live webcam clip → Thank you.

- `motion.html` — animated intro, section boxes, test-table scene, lower-third labels, thank-you. Needs the fonts
  (`npm pack @fontsource/space-grotesk @fontsource/inter @fontsource/jetbrains-mono`, copy the latin 400/500/600/700 woff2
  next to it), `docs/brand/isro.png`, and the test-table PNG from `rec_table.mjs`.
- `render.mjs <scene> <seconds> <outdir> [query] [alpha]` — renders a scene to PNG frames at 30 fps (deterministic).
- `rec_decoy.mjs` / `rec_table.mjs` — capture the Console decoy run frame by frame and the test record (serve `docs/` on :8791).
- `build_v2.sh` — joins the segments with xfade transitions.

To add MK2: render a `sec` box ("MK2 · stepper terminal"), encode the MK2 clip to `s2/mk2.mp4`
(1920×1080, 30 fps), insert both after `mk1` in the segment list, and add two transitions.
The site copies of the videos have no audio; for voice, mux the original audio in the last step.
