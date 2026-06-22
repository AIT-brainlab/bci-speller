"""Tests for the bci package skeleton and board module."""

from __future__ import annotations

import queue
import threading
import time
from unittest.mock import MagicMock

import numpy as np
import pytest

from bci.board.base import BoardInterface, BoardStatus
from bci.board.brainflow_board import BrainFlowBoard
from bci.board.stream import DataStream
from bci.board.streaming import BoardStreamLoop
from bci.board.synthetic import SyntheticBoard
from bci.processor.base import ProcessorInterface
from bci.recorder.base import RecorderInterface


def test_package_imports() -> None:
    import bci
    import bci.board
    import bci.processor
    import bci.recorder
    import bci.ui.signal_monitor
    import bci.ui.ssvep

    assert bci.BoardInterface is BoardInterface
    assert bci.DataStream is DataStream


def test_data_stream_put_get() -> None:
    stream = DataStream(maxsize=10)
    assert stream.maxsize == 10
    chunk = np.ones((8, 5))
    stream.put(chunk)
    assert np.array_equal(stream.get(), chunk)


def test_data_stream_nowait() -> None:
    stream = DataStream()
    chunk = np.zeros((4, 2))
    stream.put_nowait(chunk)
    assert stream.size == 1
    assert np.array_equal(stream.get_nowait(), chunk)


def test_board_interface_is_abc() -> None:
    with pytest.raises(TypeError):
        BoardInterface()  # type: ignore[abstract]


def test_processor_interface_is_abc() -> None:
    with pytest.raises(TypeError):
        ProcessorInterface()  # type: ignore[abstract]


def test_recorder_interface_is_abc() -> None:
    with pytest.raises(TypeError):
        RecorderInterface()  # type: ignore[abstract]


def test_board_stream_loop_forwards_chunks() -> None:
    received: list = []
    data = np.arange(12, dtype=np.float64).reshape(3, 4)

    loop = BoardStreamLoop(
        poll_buffer=lambda: data,
        put_chunk=received.append,
        poll_interval_sec=0.01,
    )
    loop.start()
    time.sleep(0.05)
    loop.stop()
    assert len(received) >= 1
    assert np.array_equal(received[0], data)


def test_brainflow_board_lifecycle() -> None:
    board = BrainFlowBoard(board_id=8, serial_number="TEST")
    assert not board.get_status().is_open
    board.open()
    assert board.get_status().is_open
    board.start_stream()
    assert board.get_status().is_streaming
    board.stop_stream()
    assert not board.get_status().is_streaming
    board.close()
    assert not board.get_status().is_open


def test_synthetic_board_streams_to_raw_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    from brainflow.board_shim import BoardShim

    call_count = 0

    def _fake_get_board_data(self: object) -> np.ndarray:
        nonlocal call_count
        call_count += 1
        return np.random.randn(32, max(1, call_count % 8 + 1))

    monkeypatch.setattr(BoardShim, "get_board_data", _fake_get_board_data)

    board = SyntheticBoard(n_channels=8, sampling_rate=250, poll_interval_sec=0.02)
    board.open()
    board.start_stream()
    try:
        chunk = board.raw_stream.get(timeout=2.0)
        assert chunk.ndim == 2
        assert chunk.shape[1] > 0
    finally:
        board.stop_stream()
        board.close()


def test_board_status_dataclass() -> None:
    status = BoardStatus(is_open=True, is_streaming=False, board_id=-1)
    assert status.is_open
    assert status.board_id == -1


def test_board_interface_subscribers() -> None:
    board = SyntheticBoard(n_channels=8, sampling_rate=250)
    assert board.get_status().board_id == -1
    stream = board.get_raw_stream()
    assert stream is not None

    stream2 = DataStream()
    board.add_subscriber(stream2)
    assert stream2 in board._subscribers

    # Try adding again (should remain unique)
    board.add_subscriber(stream2)
    
    board.remove_subscriber(stream2)
    assert stream2 not in board._subscribers

    # Remove non-existent subscriber safely
    board.remove_subscriber(stream2)

    # Verify channel indices property
    assert isinstance(board.eeg_channel_indices, tuple)


def test_board_stream_loop_extended() -> None:
    from bci.board.streaming import BoardStreamLoop
    received = []

    # Callback that returns empty on first call, then data
    call_count = 0
    def poll_buffer():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return np.empty((0, 0))
        return np.ones((8, 5))

    loop = BoardStreamLoop(
        poll_buffer=poll_buffer,
        put_chunk=received.append,
        poll_interval_sec=0.01,
    )

    assert not loop.is_running
    loop.start()
    assert loop.is_running

    time.sleep(0.05)

    # Pause
    loop.pause()
    time.sleep(0.03)

    # Resume
    loop.resume()
    time.sleep(0.03)

    # Trigger exception in put_chunk
    loop._put_chunk = MagicMock(side_effect=Exception("mock put fail"))
    time.sleep(0.03)

    loop.stop()
