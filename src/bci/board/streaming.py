"""Background thread that polls board data and pushes chunks onto raw_stream."""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray

POLL_INTERVAL_SEC = 0.05


class BoardStreamLoop:
    """
    Poll a board buffer callback and forward copies to a DataStream.

    The board supplies data via ``poll_buffer``; this loop does not know
    who consumes ``raw_stream``.
    """

    def __init__(
        self,
        poll_buffer: Callable[[], NDArray[np.float64]],
        put_chunk: Callable[[NDArray[np.float64]], None],
        poll_interval_sec: float = POLL_INTERVAL_SEC,
    ) -> None:
        self._poll_buffer = poll_buffer
        self._put_chunk = put_chunk
        self._poll_interval_sec = float(poll_interval_sec)
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        self._poll_buffer()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="BoardStreamLoop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        _ = self._poll_buffer()
        self._pause_event.set()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._pause_event.wait(timeout=self._poll_interval_sec)
            if self._stop_event.is_set():
                break
            if not self._pause_event.is_set():
                continue
            data = self._poll_buffer()
            if data is None or data.size == 0 or data.shape[1] == 0:
                time.sleep(self._poll_interval_sec)
                continue
            try:
                self._put_chunk(data.copy())
            except Exception:
                pass
