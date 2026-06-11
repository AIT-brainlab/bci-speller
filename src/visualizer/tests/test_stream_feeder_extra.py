"""Extra feeder edge-case tests."""

from __future__ import annotations

import queue
from unittest.mock import MagicMock

import numpy as np

from visualizer.stream_feeder import BoardStreamFeeder


def test_feeder_queue_full_swallowed() -> None:
    data_q: queue.Queue = queue.Queue(maxsize=1)
    data_q.put(np.zeros((2, 2)))
    board = MagicMock()
    board.get_board_data.return_value = np.ones((17, 5))

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.001)
    feeder.start()
    import time

    time.sleep(0.02)
    feeder.stop()
    assert feeder._thread is None or not feeder._thread.is_alive()


def test_feeder_stop_during_wait() -> None:
    data_q: queue.Queue = queue.Queue()
    board = MagicMock()

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.1)
    feeder.pause()
    feeder.start()
    feeder._stop_event.set()
    import time

    time.sleep(0.35)
    feeder.stop()


def test_feeder_stop_breaks_loop() -> None:
    data_q: queue.Queue = queue.Queue()
    board = MagicMock()
    board.get_board_data.return_value = np.ones((17, 3))

    feeder = BoardStreamFeeder(board, data_q, poll_interval_sec=0.05)
    feeder.start()
    import time

    feeder._stop_event.set()
    time.sleep(0.12)
    feeder.stop()
