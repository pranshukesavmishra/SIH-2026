# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the FSOC-PAT standalone application (PS SIH26169
deliverable 1, "Software Application").

    pyinstaller --noconfirm --clean packaging/fsoc-pat.spec

Produces a one-directory bundle:

    dist/fsoc-pat/fsoc-pat          (Linux/macOS)
    dist\\fsoc-pat\\fsoc-pat.exe      (Windows)

Ship the whole dist/fsoc-pat folder, zipped.

NOTE ON console=True — the application has a documented headless mode
(`fsoc-pat --headless scenario.yaml`) that prints the performance report to
stdout. A windowed build would discard that output and hide tracebacks, so the
console stays attached deliberately.
"""
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent          # repo root; spec lives in packaging/
SRC = ROOT / "src"

# Read-only data the application expects to find at run time. src/fsoc_pat/
# resources.py resolves these through sys._MEIPASS once frozen.
datas = [
    (str(ROOT / "models"), "models"),
    (str(ROOT / "scenarios"), "scenarios"),
]

# Imports performed lazily inside functions (see fsoc_pat/__main__.py and the
# optional verifier load in pipeline.py) are named explicitly rather than left
# to static analysis.
hiddenimports = [
    "fsoc_pat.gui.app",
    "fsoc_pat.runner",
    "fsoc_pat.server",
    "fsoc_pat.ai.verifier",
    "fsoc_pat.resources",
]
hiddenimports += collect_submodules("pyqtgraph")

excludes = [
    "matplotlib",
    "tkinter",
    "PyQt5",
    "PyQt6",
    "pytest",
    "IPython",
    "notebook",
]

a = Analysis(
    [str(SRC / "fsoc_pat" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="fsoc-pat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="fsoc-pat",
)
