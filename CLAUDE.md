# ZeroDrift — SIH 2026, PS26169 (ISRO), Software category

**Start here:** read `docs/LOCAL_HANDOFF.md` (current task and where we stopped), then
`docs/PROJECT_STATE.md` (canonical numbers and project map).

- The user is Aryan, team leader. Plain, simple English; short step-by-step answers; an image
  for wiring or building questions. If he says "only do X", do only X.
- Every number shown to judges (deck, video, report, site) must come from the canonical table
  in `docs/PROJECT_STATE.md` §2.
- Hidden build pages (`docs/build.html`, `preview.html`, `assembly.html`, `headbox.html`,
  `wiring.html`, `wiring3d.html`, `targets.html`) stay noindex and are never linked from
  public pages.
- `team_private/` is gitignored personal data. Never commit it.
- Arduino: `tools/rig/flash.sh beacon|pintest|rig [port]` compiles, uploads and prints the
  board's serial output (needs `arduino-cli`).
- Python engine: `pip install -e ".[gui,dev]"`, then `pytest`; GUI `python -m fsoc_pat.gui.app`.
