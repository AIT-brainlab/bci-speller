"""Tests for EEGVisualizer (process mocked)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from visualizer.live_monitor_class import EEGVisualizer


@pytest.fixture
def board_shim() -> Any:
    shim = MagicMock()
    shim.get_board_data.return_value = None
    return shim


def test_eeg_visualizer_builds_queues(board_shim: Any) -> None:
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=5,
        plot_hz=20,
        amplitude_uv=100,
    )
    assert vis.data_queue is not None
    assert vis.is_running is False


@patch("visualizer.live_monitor_class.Process")
def test_start_stop(mock_process_cls: MagicMock, board_shim: Any) -> None:
    proc = MagicMock()
    proc.is_alive.return_value = True
    mock_process_cls.return_value = proc

    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=2,
        plot_hz=10,
        amplitude_uv=80,
    )
    vis.start()
    mock_process_cls.assert_called_once()
    vis.stop()
    proc.join.assert_called()


@patch("visualizer.live_monitor_class.Process")
def test_stop_terminates_alive_process(mock_process_cls: MagicMock, board_shim: Any) -> None:
    proc = MagicMock()
    proc.is_alive.side_effect = [True, True]
    mock_process_cls.return_value = proc

    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
    )
    vis._process = proc
    vis.stop()
    proc.terminate.assert_called_once()


def test_mark_puts_label(board_shim: Any) -> None:
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
    )
    vis._marker_queue = MagicMock()
    vis.mark("cue-A")
    vis._marker_queue.put_nowait.assert_called_once_with("cue-A")


def test_pause_resume(board_shim: Any) -> None:
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
    )
    assert vis._pause_event.is_set()
    vis.pause()
    assert not vis._pause_event.is_set()
    vis.resume()
    assert vis._pause_event.is_set()


def test_mark_swallows_queue_error(board_shim: Any) -> None:
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
    )
    vis._marker_queue = MagicMock()
    vis._marker_queue.put_nowait.side_effect = RuntimeError("full")
    vis.mark("x")


def test_board_channel_fallback(monkeypatch: pytest.MonkeyPatch, board_shim: Any) -> None:
    import brainflow.board_shim as bf

    monkeypatch.setattr(
        bf.BoardShim,
        "get_sampling_rate",
        staticmethod(lambda _id: (_ for _ in ()).throw(RuntimeError())),
    )
    monkeypatch.setattr(
        bf.BoardShim,
        "get_eeg_channels",
        staticmethod(lambda _id: (_ for _ in ()).throw(RuntimeError())),
    )
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
        n_channels=4,
    )
    assert vis._proc_args[5] == [1, 2, 3, 4]
    assert vis._proc_args[7] == 250.0


def test_custom_ch_indices(board_shim: Any) -> None:
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
        ch_indices=[3, 4],
        n_channels=2,
    )
    assert vis._proc_args[5] == [3, 4]
