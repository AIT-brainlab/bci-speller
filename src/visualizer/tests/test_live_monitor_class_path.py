"""Test live_monitor_class path insertion."""

from __future__ import annotations

import sys
import importlib
from pathlib import Path

def test_live_monitor_class_path_insertion() -> None:
    # Find the _BCI_SRC path
    viz_root = Path(__file__).resolve().parents[1]
    bci_src = str(viz_root / "src")
    
    # Remove from sys.path if present
    if bci_src in sys.path:
        sys.path.remove(bci_src)
        
    # Import the module
    import live_monitor_class
    importlib.reload(live_monitor_class)
    
    # Verify it was added back
    assert bci_src in sys.path
