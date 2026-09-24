"""
Entry point for the packaged application.

    fsoc-pat                       launch the GUI on the default scenario
    fsoc-pat scenario.yaml         launch the GUI on a scenario
    fsoc-pat --headless s.yaml     run headless, print the performance report
    fsoc-pat --help                this message

This module does its own argument handling rather than deferring to the
GUI, because the GUI never had any: it read ``argv[0]`` straight into a
file open, so ``fsoc-pat --help`` died with a FileNotFoundError naming
"--help", and any typo in a path produced a traceback instead of a
sentence. For a deliverable whose first line is "a standalone executable
application", ``--help`` is the first thing anyone types.
"""
from __future__ import annotations

import pathlib
import sys

USAGE = """\
fsoc-pat -- AI-based virtual camera tracking for FSOC coarse alignment

usage:
  fsoc-pat                       launch the GUI on the default scenario
  fsoc-pat SCENARIO.yaml         launch the GUI on a scenario
  fsoc-pat --headless SCENARIO   run headless and print the report
  fsoc-pat --help                show this message

headless options are described by:
  fsoc-pat --headless --help
"""


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if "--help" in argv or "-h" in argv:
        if "--headless" in argv:
            argv.remove("--headless")
            from fsoc_pat.runner import main as headless
            return headless(argv)
        print(USAGE, end="")
        return 0

    if "--headless" in argv:
        argv.remove("--headless")
        from fsoc_pat.runner import main as headless
        return headless(argv)

    # GUI path. Validate here so a mistyped path is a sentence, not a stack.
    positional = [a for a in argv if not a.startswith("-")]
    flags = [a for a in argv if a.startswith("-")]
    if flags:
        print(f"fsoc-pat: unknown option {flags[0]!r}\n", file=sys.stderr)
        print(USAGE, end="", file=sys.stderr)
        return 2
    if len(positional) > 1:
        print(f"fsoc-pat: expected at most one scenario, got {len(positional)}\n",
              file=sys.stderr)
        print(USAGE, end="", file=sys.stderr)
        return 2
    if positional and not pathlib.Path(positional[0]).is_file():
        print(f"fsoc-pat: no such scenario file: {positional[0]}", file=sys.stderr)
        return 2

    from fsoc_pat.gui.app import main as gui
    return gui(positional)


if __name__ == "__main__":
    raise SystemExit(main())
