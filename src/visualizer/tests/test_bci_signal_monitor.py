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


def test_signal_monitor_app_exceptions() -> None:
    # 1. Mock resolve_plot_params to raise exception
    with patch("visualizer.config.settings.resolve_plot_params", side_effect=Exception("resolve error")):
        app = SignalMonitorApp(
            board_id=8,
            window_sec=5.0,
            plot_hz=20,
            amplitude_uv=100.0,
        )
        assert app._proc_args[6] == 5.0

    # 2. Mock board whose get_status raises exception
    bad_board = MagicMock()
    bad_board.get_status.side_effect = Exception("status error")
    del bad_board.eeg_channel_indices
    del bad_board.get_raw_stream
    bad_board.raw_stream = DataStream()
    
    app2 = SignalMonitorApp(board=bad_board, n_channels=4)
    assert app2._proc_args[4] == 4
    
    # 3. Test stop with bridge
    app2.stop()


def test_position_figure_on_monitor() -> None:
    from bci.ui.signal_monitor.widgets import position_figure_on_monitor

    # 1. Test when root is None (covers line 122)
    fig_none = MagicMock()
    del fig_none.canvas.manager.window
    fig_none.canvas.get_tk_widget.side_effect = Exception("no tk")
    position_figure_on_monitor(fig_none, 0)

    # 2. Test fallback to get_tk_widget (covers lines 87-91)
    fig_tk = MagicMock()
    del fig_tk.canvas.manager.window
    root = MagicMock()
    widget = MagicMock()
    widget.winfo_toplevel.return_value = root
    fig_tk.canvas.get_tk_widget.return_value = widget

    with patch("bci.ui.signal_monitor.widgets.list_monitors", return_value=[(0, 0, 1920, 1080)]):
        position_figure_on_monitor(fig_tk, 0)
        assert root.geometry.called
