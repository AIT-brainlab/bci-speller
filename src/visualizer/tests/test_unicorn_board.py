"""Tests for the UnicornBoard."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from bci.board.unicorn import (
    UNICORN_BOARD_ID,
    UNICORN_CHANNEL_NAMES,
    UNICORN_SAMPLING_RATE,
    UnicornBoard,
)


def test_unicorn_board_default_construction() -> None:
    board = UnicornBoard()
    assert board._board_id == UNICORN_BOARD_ID
    assert board.channel_names == UNICORN_CHANNEL_NAMES


def test_unicorn_board_with_serial_number(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_params = None
    
    # We patch BrainFlowBoard's local import of BoardShim
    # but the easiest way is to mock BoardShim.__init__
    from brainflow.board_shim import BoardShim
    original_init = BoardShim.__init__
    
    def fake_init(self, board_id, params):
        nonlocal captured_params
        captured_params = params
        original_init(self, board_id, params)
        
    monkeypatch.setattr(BoardShim, "__init__", fake_init)
    
    board = UnicornBoard(serial_number="UN-2021.05.51")
    assert captured_params is not None
    assert captured_params.serial_number == "UN-2021.05.51"


def test_unicorn_board_get_status() -> None:
    board = UnicornBoard()
    status = board.get_status()
    assert status.is_open is False
    assert status.is_streaming is False
    assert status.board_id == UNICORN_BOARD_ID
    assert status.sampling_rate == UNICORN_SAMPLING_RATE
    assert status.n_channels == 8


def test_unicorn_board_channel_names() -> None:
    board = UnicornBoard()
    assert board.channel_names == [
        "Fz",
        "C3",
        "Cz",
        "C4",
        "Pz",
        "PO7",
        "Oz",
        "PO8",
    ]


def test_unicorn_board_streams_to_raw_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    from brainflow.board_shim import BoardShim

    call_count = 0

    def _fake_get_board_data(self: object) -> np.ndarray:
        nonlocal call_count
        call_count += 1
        return np.random.randn(32, max(1, call_count % 8 + 1))

    # Mock get_board_data to return some fake data
    monkeypatch.setattr(BoardShim, "get_board_data", _fake_get_board_data)
    # Mock prepare_session so it does not fail without actual hardware
    monkeypatch.setattr(BoardShim, "prepare_session", MagicMock())
    # Mock start_stream so it does not fail without actual hardware
    monkeypatch.setattr(BoardShim, "start_stream", MagicMock())
    # Mock stop_stream and release_session as well
    monkeypatch.setattr(BoardShim, "stop_stream", MagicMock())
    monkeypatch.setattr(BoardShim, "release_session", MagicMock())

    board = UnicornBoard(poll_interval_sec=0.02)
    board.open()
    board.start_stream()
    try:
        chunk = board.raw_stream.get(timeout=2.0)
        assert chunk.ndim == 2
        assert chunk.shape[1] > 0
    finally:
        board.stop_stream()
        board.close()
