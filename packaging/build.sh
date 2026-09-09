#!/usr/bin/env bash
# Build the FSOC-PAT standalone application on Linux.
# Run from the repository root:  packaging/build.sh
set -euo pipefail
python3 -m venv .venv-build 2>/dev/null || true
source .venv-build/bin/activate
pip install -q -e . pyinstaller PySide6 pyqtgraph
pyinstaller --noconfirm --clean --onefile --noconsole --name fsoc-pat \
    --distpath dist --workpath build packaging/entry_gui.py
echo
echo "Build complete: dist/fsoc-pat/fsoc-pat"
