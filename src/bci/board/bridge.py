"""Forward chunks from a thread-safe DataStream to a multiprocessing queue."""

from __future__ import annotations

import queue
import threading
import time
from typing import Any, Optional

from bci.board.stream import DataStream

BRIDGE_POLL_SEC = 0.01


class StreamBridge:
    """
    Background thread: read ``DataStream`` chunks and forward to an mp.Queue.

    Used so the matplotlib child process can consume board data on Windows
    without running Tkinter off the main thread.
    """

    def __init__(
        self,
        source: DataStream,
        dest: Any,
        poll_interval_sec: float = BRIDGE_POLL_SEC,
    ) -> None:
        self._source = source
        self._dest = dest
        self._poll_interval_sec = float(poll_interval_sec)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="StreamBridge",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                chunk = self._source.get(timeout=self._poll_interval_sec)
            except queue.Empty:
                continue
            try:
                self._dest.put_nowait(chunk)
            except Exception:
                pass
