"""Ensure bci and visualizer are importable in spawned child processes (Windows)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_bci_paths() -> None:
    """Add project root and src/ to sys.path for multiprocessing spawn."""
    viz_root = Path(__file__).resolve().parents[2]
    src_root = viz_root / "src"
    for path in (viz_root.parent, src_root, viz_root):
        entry = str(path)
        if entry not in sys.path:
            sys.path.insert(0, entry)
