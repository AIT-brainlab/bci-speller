"""Extra process tests for buffer and UI edge paths."""

from __future__ import annotations

import multiprocessing
from unittest.mock import MagicMock, patch

import numpy as np

from visualizer.tests.test_process import _matplotlib_test_env
from visualizer.process import run_visualizer_process


@patch("visualizer.process.position_figure_on_monitor")
def test_run_process_large_and_small_chunks(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    small = np.random.randn(17, 10)
    large = np.random.randn(17, 500)
    data_q.put(large)
    data_q.put(small)

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=2,
        ch_indices=[1, 2],
        window_sec=1.0,
        fs=250.0,
        plot_hz=20,
        amplitude_uv=100.0,
        labels=["Fz", "C3"],
        monitor_index=0,
    )

    assert len(stubs.callbacks) >= 1
    mock_position.assert_called_once()
