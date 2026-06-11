"""Additional process tests for 100% coverage."""

from __future__ import annotations

import multiprocessing
import time
from unittest.mock import MagicMock, patch

import numpy as np

from visualizer.tests.test_process import _matplotlib_test_env
from visualizer.process import run_visualizer_process


@patch("visualizer.process.position_figure_on_monitor")
def test_process_marker_skips_text_when_no_axes(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()
    marker_q.put("cue")

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=0,
        ch_indices=[],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=50.0,
        labels=[],
        monitor_index=0,
    )

    stubs.callbacks[0](0)
    mock_position.assert_called_once()


@patch("visualizer.process.position_figure_on_monitor")
def test_process_ui_exceptions(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    stubs.fig.canvas.manager.set_window_title.side_effect = RuntimeError("no title")
    stubs.fig.tight_layout.side_effect = RuntimeError("layout")
    stubs.plt.show.side_effect = RuntimeError("display failed")

    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()
    data_q.put(np.full((17, 50), 200.0))

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=3,
        ch_indices=[1, 2, 3],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=50.0,
        labels=["A", "B", "C"],
        monitor_index=0,
    )
    mock_position.assert_called_once()


@patch("visualizer.process.position_figure_on_monitor")
def test_process_quality_colors_and_hz(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=3,
        ch_indices=[1, 2, 3],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=50.0,
        labels=["A", "B", "C"],
        monitor_index=0,
    )

    buf_n = 250
    data_q.put(np.full((17, buf_n), 30.0))
    stubs.callbacks[0](0)

    data_q.put(np.full((17, buf_n), 8.0))
    stubs.callbacks[0](0)

    data_q.put(np.full((17, buf_n), 2.0))
    stubs.callbacks[0](0)

    data_q.put(np.full((17, buf_n), 0.2))
    stubs.callbacks[0](0)

    stop_event.set()
    stubs.plt.close.side_effect = RuntimeError("close")
    stubs.callbacks[0](0)
    mock_position.assert_called_once()


@patch("visualizer.process.position_figure_on_monitor")
def test_process_status_ok_color(mock_position: MagicMock) -> None:
    """Cover quality branch: 0.15 < quality <= 0.8 (STATUS_OK)."""
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=1,
        ch_indices=[1],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=100.0,
        labels=["Fz"],
        monitor_index=0,
    )
    data_q.put(np.full((17, 250), 20.0))
    stubs.callbacks[0](0)

    data_q.put(np.full((17, 250), 4.0))
    marker_q.put("cue")
    stubs.callbacks[0](0)


@patch("visualizer.process.position_figure_on_monitor")
def test_process_status_pause_only(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=1,
        ch_indices=[1],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=100.0,
        labels=["Fz"],
        monitor_index=0,
    )
    data_q.put(np.full((17, 250), 5.0))
    marker_q.put("pause")
    stubs.callbacks[0](0)


@patch("visualizer.process.position_figure_on_monitor")
def test_process_live_hz_counter(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    with patch(
        "visualizer.process.time.perf_counter",
        side_effect=[1000.0, 1000.0, 1002.0, 1002.0, 1002.0, 1002.0],
    ):
        run_visualizer_process(
            data_q,
            marker_q,
            stop_event,
            pause_event,
            n_channels=1,
            ch_indices=[1],
            window_sec=1.0,
            fs=250.0,
            plot_hz=10,
            amplitude_uv=50.0,
            labels=["Fz"],
            monitor_index=0,
        )
        data_q.put(np.ones((17, 20)))
        stubs.callbacks[0](0)

    mock_position.assert_called_once()


@patch("visualizer.process.position_figure_on_monitor")
def test_process_paused_status(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = multiprocessing.Queue()
    marker_q: multiprocessing.Queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()

    run_visualizer_process(
        data_q,
        marker_q,
        stop_event,
        pause_event,
        n_channels=1,
        ch_indices=[1],
        window_sec=1.0,
        fs=250.0,
        plot_hz=10,
        amplitude_uv=50.0,
        labels=["Fz"],
        monitor_index=0,
    )
    stubs.callbacks[0](0)

