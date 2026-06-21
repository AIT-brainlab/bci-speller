
from __future__ import annotations

import sys
from pathlib import Path

# Allow "Run" on this file from the IDE.
if __name__ == "__main__":
    _internship_root = Path(__file__).resolve().parent.parent
    if str(_internship_root) not in sys.path:
        sys.path.insert(0, str(_internship_root))

from visualizer.config import (
    VisualizerConfigError,
    VisualizerSettings,
    get_visualizer_settings,
    resolve_plot_params,
)
from visualizer.live_monitor_class import EEGVisualizer
from visualizer.process import _run_visualizer_process, run_visualizer_process

__all__ = [
    "EEGVisualizer",
    "VisualizerConfigError",
    "VisualizerSettings",
    "get_visualizer_settings",
    "resolve_plot_params",
    "run_visualizer_process",
    "_run_visualizer_process",
]


if __name__ == "__main__":
    import multiprocessing

    from visualizer.standalone import run_standalone

    multiprocessing.freeze_support()
    raise SystemExit(run_standalone())
