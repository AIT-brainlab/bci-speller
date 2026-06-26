"""Cover live_monitor.py __main__ entry and live_monitor_class branches."""

from __future__ import annotations

import multiprocessing
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from visualizer.live_monitor_class import EEGVisualizer


@pytest.fixture
def board_shim() -> MagicMock:
    shim = MagicMock()
    shim.get_board_data.return_value = None
    return shim


def test_live_monitor_main_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    internship_root = Path(__file__).resolve().parents[2]
    root_str = str(internship_root)
    monkeypatch.delitem(sys.modules, "visualizer.live_monitor", raising=False)
    sys.path[:] = [p for p in sys.path if p != root_str]

    with patch("multiprocessing.freeze_support") as freeze:
        with patch("visualizer.standalone.run_standalone", return_value=0) as run:
            with pytest.raises(SystemExit) as exc:
                runpy.run_module(
                    "visualizer.live_monitor",
                    run_name="__main__",
                    alter_sys=True,
                )
    assert exc.value.code == 0
    freeze.assert_called_once()
    run.assert_called_once()
    assert root_str in sys.path


def test_live_monitor_main_skips_path_insert_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_str = str(Path(__file__).resolve().parents[2])
    monkeypatch.delitem(sys.modules, "visualizer.live_monitor", raising=False)
    sys.path[:] = [p for p in sys.path if p != root_str]
    sys.path.insert(0, root_str)

    with patch("multiprocessing.freeze_support"):
        with patch("visualizer.standalone.run_standalone", return_value=0):
            with pytest.raises(SystemExit):
                runpy.run_module(
                    "visualizer.live_monitor",
                    run_name="__main__",
                    alter_sys=True,
                )


def test_stop_when_process_not_alive(board_shim: MagicMock) -> None:
    proc = MagicMock()
    proc.is_alive.return_value = False
    vis = EEGVisualizer(
        board_shim=board_shim,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
    )
    vis._process = proc
    vis.stop()
    proc.join.assert_not_called()
    proc.terminate.assert_not_called()


@patch("bci.ui.signal_monitor.app.Process")
def test_stop_join_without_terminate(mock_process_cls: MagicMock) -> None:
    proc = MagicMock()
    proc.is_alive.side_effect = [True, False]
    mock_process_cls.return_value = proc

    board = MagicMock()
    vis = EEGVisualizer(
        board_shim=board,
        board_id=8,
        window_sec=1,
        plot_hz=5,
        amplitude_uv=50,
        fs=500,
    )
    vis._process = proc
    vis.stop()
    proc.terminate.assert_not_called()


def test_eeg_visualizer_uses_board_sampling_rate(board_shim: MagicMock) -> None:
    import brainflow.board_shim as bf

    with patch.object(bf.BoardShim, "get_sampling_rate", return_value=128):
        vis = EEGVisualizer(
            board_shim=board_shim,
            board_id=8,
            window_sec=1,
            plot_hz=5,
            amplitude_uv=50,
        )
    assert vis._proc_args[7] == 128.0
