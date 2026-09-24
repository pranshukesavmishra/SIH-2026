"""Locate bundled data from a source checkout, an installed package, or a
PyInstaller bundle.

A frozen build unpacks its data under ``sys._MEIPASS``; a source checkout keeps
it at the repository root. Call sites that hard-code ``__file__``-relative
parent walks work in the second case and silently break in the first — the
packaged application loading its AI verifier weights is exactly that bug.
Everything that reads shipped data should go through here instead.

Read-only shipped data → :func:`bundled`.
Anything the program writes → :func:`writable_dir` (never inside the bundle,
which may be a temporary or read-only directory).
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import List

_HERE = pathlib.Path(__file__).resolve().parent          # .../src/fsoc_pat


def _candidate_roots() -> List[pathlib.Path]:
    """Directories that may hold ``models/`` and ``scenarios/``, best first."""
    roots: List[pathlib.Path] = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:                                   # PyInstaller, onefile or onedir
        roots.append(pathlib.Path(meipass))
    if getattr(sys, "frozen", False):             # alongside the executable
        roots.append(pathlib.Path(sys.executable).resolve().parent)

    roots.append(_HERE.parents[1])                # repo root, from src/fsoc_pat
    roots.append(_HERE.parent)                    # src/, if data sits beside it
    roots.append(pathlib.Path.cwd())

    seen, unique = set(), []
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique.append(root)
    return unique


def bundled(*parts: str) -> pathlib.Path:
    """Path to read-only shipped data, e.g. ``bundled("scenarios")``.

    Returns the first candidate that exists. If none do, returns the path under
    the most likely root so callers can still report a sensible missing-file
    error — or test ``.exists()`` and degrade, as the verifier loader does.
    """
    relative = pathlib.Path(*parts)
    roots = _candidate_roots()
    for root in roots:
        candidate = root / relative
        if candidate.exists():
            return candidate
    return roots[0] / relative


def model(name: str = "track_verifier.npz") -> pathlib.Path:
    """Trained network weights shipped with the application."""
    return bundled("models", name)


def scenarios_dir() -> pathlib.Path:
    return bundled("scenarios")


def default_scenario() -> pathlib.Path:
    return bundled("scenarios", "leo_pass_nominal.yaml")


def writable_dir(*parts: str) -> pathlib.Path:
    """A per-user directory the application may write to, created on demand.

    Override the base with ``FSOC_PAT_HOME``. Used for anything generated at
    runtime: a frozen bundle's own directory is not writable.
    """
    base = os.environ.get("FSOC_PAT_HOME")
    root = pathlib.Path(base) if base else pathlib.Path.home() / ".fsoc-pat"
    target = root.joinpath(*parts)
    target.mkdir(parents=True, exist_ok=True)
    return target
