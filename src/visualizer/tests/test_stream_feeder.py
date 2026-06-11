"""Tests for BoardStreamFeeder."""

from __future__ import annotations

import queue
from unittest.mock import MagicMock

import numpy as np

from visualizer.stream_feeder import BoardStreamFeeder


def test_feeder_pushes_data() -> None:
    data_q: queue.Queue = queue.Queue()
    board = MagicMock()
    board.get_board_data.return_value = np.ones((17, 50))

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.001)
    feeder.start()
    try:
        chunk = data_q.get(timeout=2.0)
        assert chunk.shape == (17, 50)
    finally:
        feeder.stop()


def test_feeder_pause_skips_queue() -> None:
    data_q: queue.Queue = queue.Queue()
    board = MagicMock()
    board.get_board_data.return_value = np.ones((17, 10))

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.001)
    feeder.start()
    import time

    time.sleep(0.03)
    while not data_q.empty():
        data_q.get_nowait()
    feeder.pause()
    time.sleep(0.08)
    size_while_paused = data_q.qsize()
    time.sleep(0.08)
    assert data_q.qsize() == size_while_paused
    feeder.resume()
    try:
        chunk = data_q.get(timeout=2.0)
        assert chunk.shape[1] == 10
    finally:
        feeder.stop()


def test_feeder_skips_empty_board_data() -> None:
    data_q: queue.Queue = queue.Queue()
    board = MagicMock()
    board.get_board_data.return_value = np.zeros((17, 0))

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.001)
    feeder.start()
    import time

    time.sleep(0.05)
    feeder.stop()
    assert data_q.empty()
