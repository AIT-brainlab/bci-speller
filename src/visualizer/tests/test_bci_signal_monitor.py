"""Tests for bci.ui.signal_monitor (process mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bci.board.stream import DataStream
from bci.ui.signal_monitor.app import SignalMonitorApp


def test_signal_monitor_app_constructs() -> None:
    app = SignalMonitorApp(
        board_id=8,
        n_channels=8,
        window_sec=5.0,
        plot_hz=20,
        amplitude_uv=100.0,
    )
    assert app.data_queue is not None
    assert app.is_running is False


@patch("bci.ui.signal_monitor.app.Process")
def test_start_stop(mock_process_cls: MagicMock) -> None:
    proc = MagicMock()
    proc.is_alive.return_value = True
    mock_process_cls.return_value = proc

    app = SignalMonitorApp(
        board_id=8,
        window_sec=2,
        plot_hz=10,
        amplitude_uv=80,
    )
    app.start()
    mock_process_cls.assert_called_once()
    app.stop()
    proc.join.assert_called()


@patch("bci.ui.signal_monitor.app.Process")
def test_start_with_board_starts_bridge(mock_process_cls: MagicMock) -> None:
    proc = MagicMock()
    proc.is_alive.return_value = True
    mock_process_cls.return_value = proc

    board = MagicMock()
    board.raw_stream = DataStream()
    board.get_status.return_value = MagicMock(
        board_id=-1, sampling_rate=250, n_channels=8,
    )
    board.eeg_channel_indices = tuple(range(1, 9))

    app = SignalMonitorApp(board=board, window_sec=1, plot_hz=5, amplitude_uv=50)
    with patch.object(app._bridge, "start") as mock_bridge_start:
        app.start()
        mock_bridge_start.assert_called_once()


def test_mark_queues_label() -> None:
    app = SignalMonitorApp(board_id=8, window_sec=1, plot_hz=5, amplitude_uv=50)
    app._marker_queue = MagicMock()
    app.mark("cue-A")
    app._marker_queue.put_nowait.assert_called_once_with("cue-A")


def test_pause_resume() -> None:
    app = SignalMonitorApp(board_id=8, window_sec=1, plot_hz=5, amplitude_uv=50)
    assert app._pause_event.is_set()
    app.pause()
    assert not app._pause_event.is_set()
    app.resume()
    assert app._pause_event.is_set()


def test_stop_before_start() -> None:
    app = SignalMonitorApp(board_id=8, window_sec=1, plot_hz=5, amplitude_uv=50)
    app.stop()
    assert not app.is_running
