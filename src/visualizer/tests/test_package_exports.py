"""Smoke tests for public package API."""

from __future__ import annotations

import visualizer
from visualizer.live_monitor_class import EEGVisualizer


def test_public_exports() -> None:
    assert visualizer.EEGVisualizer is EEGVisualizer
    assert "resolve_plot_params" in visualizer.__all__


def test_lazy_run_standalone() -> None:
    from visualizer.standalone import run_standalone as direct

    assert visualizer.run_standalone is direct


def test_live_monitor_module_exports() -> None:
    import visualizer.live_monitor as lm

    assert lm.EEGVisualizer is EEGVisualizer
    assert lm.run_visualizer_process is not None
    assert "get_visualizer_settings" in lm.__all__