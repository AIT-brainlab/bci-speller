"""Shared import path setup for scripts run from any working directory."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def bootstrap() -> Path:
    """
    Insert paths needed for ``bci`` and ``visualizer`` imports.

    ``visualizer`` is the project folder name, so its parent must be on
    sys.path (same as ``experiment.py``). ``bci`` lives under ``src/``.
    """
    for path in (_PROJECT_ROOT.parent, _PROJECT_ROOT / "src", _PROJECT_ROOT):
        entry = str(path)
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return _PROJECT_ROOT
