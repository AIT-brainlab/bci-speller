"""Tests for bci.ui.signal_monitor.process."""

from __future__ import annotations

import importlib
import multiprocessing
import queue
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bci.ui.signal_monitor.process import run_signal_monitor_process

@pytest.fixture
def mock_queues() -> tuple[multiprocessing.Queue, multiprocessing.Queue]:
    return MagicMock(), MagicMock()


def test_signal_monitor_process_import_path_branch() -> None:
    import bci.ui.signal_monitor.process as process_mod
    process_path = Path(process_mod.__file__).resolve()
    viz_root = process_path.parents[4]
    src_root = viz_root / "src"
    entries = [str(viz_root.parent), str(src_root), str(viz_root)]

    saved_path = list(sys.path)
    try:
        for entry in entries:
            while entry in sys.path:
                sys.path.remove(entry)
        importlib.reload(process_mod)
    finally:
        sys.path[:] = saved_path


def test_signal_monitor_process_high_quality_branch(mock_queues: tuple) -> None:
    data_queue, marker_queue = mock_queues
    stop_event = MagicMock()
    stop_event.is_set.return_value = False
    pause_event = MagicMock()
    pause_event.is_set.return_value = True

    mock_plt = MagicMock()
    mock_animation_module = MagicMock()
    mock_gridspec = MagicMock()

    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_plt.figure.return_value = mock_fig
    mock_fig.add_subplot.return_value = mock_ax

    mock_line = MagicMock()
    mock_ax.plot.return_value = [mock_line]
    mock_ax.fill.return_value = [mock_line]

    import numpy as np
    data_queue.get_nowait.side_effect = [np.ones((1, 300)) * 100, Exception("break")]
    marker_queue.get_nowait.side_effect = [Exception("break")]

    update_func = None
    def capture_update(fig, func, **kwargs):
        nonlocal update_func
        update_func = func
        return MagicMock()
    mock_animation_module.FuncAnimation.side_effect = capture_update

    modules = {
        "matplotlib.pyplot": mock_plt,
        "matplotlib.animation": mock_animation_module,
        "matplotlib.gridspec": mock_gridspec,
    }

    with patch.dict("sys.modules", modules):
        with patch("bci.ui.signal_monitor.process.time.perf_counter", side_effect=[0.0, 1.1]):
            run_signal_monitor_process(
                data_q=data_queue,
                marker_q=marker_queue,
                stop_event=stop_event,
                pause_event=pause_event,
                n_channels=1,
                ch_indices=[0],
                window_sec=1.0,
                fs=250.0,
                plot_hz=10,
                amplitude_uv=100.0,
                labels=["C1"],
                monitor_index=1,
            )

    assert update_func is not None
    update_func(0)
    mock_plt.show.assert_called_once()


def test_signal_monitor_process_axes_false_marker_branch(mock_queues: tuple) -> None:
    data_queue, marker_queue = mock_queues
    stop_event = MagicMock()
    stop_event.is_set.return_value = False
    pause_event = MagicMock()
    pause_event.is_set.return_value = True

    mock_plt = MagicMock()
    mock_animation_module = MagicMock()
    mock_gridspec = MagicMock()

    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_plt.figure.return_value = mock_fig
    mock_fig.add_subplot.return_value = mock_ax

    mock_line = MagicMock()
    mock_ax.plot.return_value = [mock_line]
    mock_ax.fill.return_value = [mock_line]

    import numpy as np
    data_queue.get_nowait.side_effect = [np.empty((0, 0)), Exception("break")]
    marker_queue.get_nowait.side_effect = ["M", Exception("break")]

    update_func = None
    def capture_update(fig, func, **kwargs):
        nonlocal update_func
        update_func = func
        return MagicMock()
    mock_animation_module.FuncAnimation.side_effect = capture_update

    modules = {
        "matplotlib.pyplot": mock_plt,
        "matplotlib.animation": mock_animation_module,
        "matplotlib.gridspec": mock_gridspec,
    }

    with patch.dict("sys.modules", modules):
        with patch("bci.ui.signal_monitor.process.time.perf_counter", side_effect=[0.0, 1.1]):
            run_signal_monitor_process(
                data_q=data_queue,
                marker_q=marker_queue,
                stop_event=stop_event,
                pause_event=pause_event,
                n_channels=0,
                ch_indices=[],
                window_sec=1.0,
                fs=250.0,
                plot_hz=10,
                amplitude_uv=100.0,
                labels=[],
                monitor_index=1,
            )

    assert update_func is not None
    update_func(0)
    mock_plt.show.assert_called_once()

def test_run_signal_monitor_process(mock_queues: tuple) -> None:
    data_queue, marker_queue = mock_queues
    stop_event = MagicMock()
    stop_event.is_set.return_value = False
    pause_event = MagicMock()
    pause_event.is_set.return_value = True

    mock_plt = MagicMock()
    mock_animation_module = MagicMock()
    mock_gridspec = MagicMock()

    # Setup mock axes
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_plt.figure.return_value = mock_fig
    mock_fig.add_subplot.return_value = mock_ax
    
    mock_line = MagicMock()
    mock_ax.plot.return_value = [mock_line]
    mock_ax.fill.return_value = [mock_line]

    import numpy as np
    chunk = np.ones((4, 10))
    data_queue.get_nowait.side_effect = [chunk, Exception("break")]
    marker_queue.get_nowait.side_effect = ["test", Exception("break")]

    update_func = None
    def capture_update(fig, func, **kwargs):
        nonlocal update_func
        update_func = func
        return MagicMock()
    mock_animation_module.FuncAnimation.side_effect = capture_update

    modules = {
        "matplotlib.pyplot": mock_plt,
        "matplotlib.animation": mock_animation_module,
        "matplotlib.gridspec": mock_gridspec
    }

    with patch.dict("sys.modules", modules):
        with patch("bci.ui.signal_monitor.process.time.perf_counter", side_effect=[0.0, 1.0, 2.1, 3.2, 4.3, 5.4, 6.5, 7.6, 8.7]):
            run_signal_monitor_process(
                data_q=data_queue,
                marker_q=marker_queue,
                stop_event=stop_event,
                pause_event=pause_event,
                n_channels=4,
                ch_indices=[0, 1, 2, 3],
                window_sec=1.0,
                fs=250.0,
                plot_hz=10,
                amplitude_uv=100.0,
                labels=["C1", "C2", "C3", "C4"],
                monitor_index=1
            )

    mock_plt.show.assert_called_once()
    assert update_func is not None

    with patch.dict("sys.modules", modules):
        with patch("bci.ui.signal_monitor.process.time.perf_counter", side_effect=[10.0, 11.1, 12.2, 13.3, 14.4, 15.5, 16.6, 17.7, 18.8]):
            # Trigger update where it reads data and updates lines
            update_func(0)

            # Branch where RMS < 1.0
            data_queue.get_nowait.side_effect = [np.zeros((4, 300)), Exception("break")]
            update_func(1)

            # Branch where RMS quality is mid
            data_queue.get_nowait.side_effect = [np.ones((4, 300)) * 20, Exception("break")]
            update_func(2)

            # Branch where RMS quality is high >0.8
            data_queue.get_nowait.side_effect = [np.ones((4, 300)) * 100, Exception("break")]
            update_func(3)

            # Branch where RMS quality is low but above stop threshold
            data_queue.get_nowait.side_effect = [np.ones((4, 300)) * 2, Exception("break")]
            update_func(4)

            # Marker label and axes text branch
            pause_event.is_set.return_value = True
            marker_queue.get_nowait.side_effect = ["M1", Exception("break")]
            update_func(5)

            # Pause event false
            pause_event.is_set.return_value = False
            update_func(6)

            # Stop event true -> closes
            stop_event.is_set.return_value = True
            mock_plt.close.side_effect = None
            update_func(7)

            # Stop event true, but close throws exception
            mock_plt.close.side_effect = Exception("err")
            update_func(8)

def test_run_signal_monitor_process_exception(mock_queues: tuple) -> None:
    data_queue, marker_queue = mock_queues
    stop_event = MagicMock()
    pause_event = MagicMock()

    mock_plt = MagicMock()
    mock_animation_module = MagicMock()
    mock_gridspec = MagicMock()

    mock_plt.show.side_effect = Exception("Test crash")
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_plt.figure.return_value = mock_fig
    mock_fig.add_subplot.return_value = mock_ax
    
    mock_line = MagicMock()
    mock_ax.plot.return_value = [mock_line]
    mock_ax.fill.return_value = [mock_line]
    
    mock_fig.canvas.manager.set_window_title.side_effect = Exception("fail")

    modules = {
        "matplotlib.pyplot": mock_plt,
        "matplotlib.animation": mock_animation_module,
        "matplotlib.gridspec": mock_gridspec
    }

    with patch.dict("sys.modules", modules):
        run_signal_monitor_process(
            data_q=data_queue,
            marker_q=marker_queue,
            stop_event=stop_event,
            pause_event=pause_event,
            n_channels=2,
            ch_indices=[0, 1],
            window_sec=1.0,
            fs=250.0,
            plot_hz=10,
            amplitude_uv=100.0,
            labels=["C1", "C2"],
            monitor_index=1
        )
    mock_plt.show.assert_called_once()
