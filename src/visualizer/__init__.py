"""
EEG live visualizer package.

Standalone::

    python -m visualizer

In experiments::

    from visualizer import EEGVisualizer
    from visualizer.live_monitor_class import EEGVisualizer
"""

from __future__ import annotations

from visualizer.config import (
    VisualizerConfigError,
    VisualizerSettings,
    get_visualizer_settings,
    resolve_plot_params,
)
from visualizer.live_monitor_class import EEGVisualizer
from visualizer.process import run_visualizer_process
from visualizer.standalone import run_standalone
from visualizer.stream_feeder import BoardStreamFeeder

__all__ = [
    "EEGVisualizer",
    "BoardStreamFeeder",
    "VisualizerConfigError",
    "VisualizerSettings",
    "get_visualizer_settings",
    "resolve_plot_params",
    "run_visualizer_process",
    "run_standalone",
]
