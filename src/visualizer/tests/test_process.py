"""Tests for run_visualizer_process with matplotlib mocked."""

from __future__ import annotations

import multiprocessing
import queue
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Callable, List
from unittest.mock import MagicMock, patch

import numpy as np

from visualizer.process import run_visualizer_process


def _make_ax() -> MagicMock:
    ax = MagicMock()
    ax.text.return_value = MagicMock()
    ax.plot.return_value = (MagicMock(),)
    ax.fill.return_value = (MagicMock(),)
    return ax


def _matplotlib_test_env() -> SimpleNamespace:
    """Build stub matplotlib modules (clears any prior matplotlib imports)."""
    for name in list(sys.modules):
        if name == "matplotlib" or name.startswith("matplotlib."):
            del sys.modules[name]

    fig = MagicMock()
    fig.add_subplot.side_effect = lambda *args, **kwargs: _make_ax()

    gs = MagicMock()
    gs.__getitem__ = MagicMock(return_value=MagicMock())

    plt = MagicMock()
    plt.figure.return_value = fig
    plt.rcParams.update = MagicMock()
    plt.show = MagicMock()
    plt.close = MagicMock()
    plt.Rectangle = MagicMock

    gridspec = MagicMock()
    gridspec.GridSpec.return_value = gs

    callbacks: List[Callable[[int], Any]] = []

    def _func_animation(_fig: MagicMock, func: Callable[[int], Any], **_kwargs: object) -> MagicMock:
        callbacks.append(func)
        func(0)
        return MagicMock()

    animation = MagicMock()
    animation.FuncAnimation.side_effect = _func_animation

    mpl = ModuleType("matplotlib")
    mpl.use = MagicMock()

    sys.modules["matplotlib"] = mpl
    sys.modules["matplotlib.pyplot"] = plt
    sys.modules["matplotlib.gridspec"] = gridspec
    sys.modules["matplotlib.animation"] = animation

    return SimpleNamespace(plt=plt, fig=fig, callbacks=callbacks)


@patch("visualizer.process.position_figure_on_monitor")
def test_run_process_live_update(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = queue.Queue()  # type: ignore
    marker_q: multiprocessing.Queue = queue.Queue()  # type: ignore
    stop_event = multiprocessing.Event()
    pause_event = multiprocessing.Event()
    pause_event.set()

    chunk = np.random.randn(17, 30)
    data_q.put(chunk)
    marker_q.put("M1")

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

    stubs.plt.show.assert_called_once()
    mock_position.assert_called_once()
    assert stubs.callbacks


@patch("visualizer.process.position_figure_on_monitor")
def test_run_process_paused_and_stopped(mock_position: MagicMock) -> None:
    stubs = _matplotlib_test_env()
    data_q: multiprocessing.Queue = queue.Queue()  # type: ignore
    marker_q: multiprocessing.Queue = queue.Queue()  # type: ignore
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

    stop_event.set()
    stubs.callbacks[0](1)
    stubs.plt.close.assert_called()
