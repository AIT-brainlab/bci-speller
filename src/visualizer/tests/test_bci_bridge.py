"""Tests for StreamBridge."""

from __future__ import annotations

import multiprocessing
import time

import numpy as np

from bci.board.bridge import StreamBridge
from bci.board.stream import DataStream


def test_stream_bridge_forwards_chunks() -> None:
    source = DataStream()
    dest = multiprocessing.Queue(maxsize=10)
    bridge = StreamBridge(source, dest, poll_interval_sec=0.01)

    chunk = np.ones((8, 5))
    source.put_nowait(chunk)
    bridge.start()
    try:
        received = dest.get(timeout=2.0)
        assert np.array_equal(received, chunk)
    finally:
        bridge.stop()


def test_stream_bridge_exception() -> None:
    from unittest.mock import MagicMock
    source = DataStream()
    dest = MagicMock()
    dest.put_nowait.side_effect = Exception("mock put fail")

    bridge = StreamBridge(source, dest, poll_interval_sec=0.01)
    bridge.start()
    source.put(np.zeros((8, 1)))
    time.sleep(0.05)
    bridge.stop()
