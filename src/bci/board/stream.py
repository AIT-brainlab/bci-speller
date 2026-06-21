"""Raw data stream abstraction wrapping a thread-safe queue."""

from __future__ import annotations

import queue
from typing import Any, Optional

DEFAULT_STREAM_MAXSIZE = 300


class DataStream:
    """Thread-safe queue for board sample chunks consumed by subscribers."""

    def __init__(self, maxsize: int = DEFAULT_STREAM_MAXSIZE) -> None:
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=maxsize)

    def put(
        self,
        chunk: Any,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        self._queue.put(chunk, block=block, timeout=timeout)

    def put_nowait(self, chunk: Any) -> None:
        self._queue.put_nowait(chunk)

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Any:
        return self._queue.get(block=block, timeout=timeout)

    def get_nowait(self) -> Any:
        return self._queue.get_nowait()

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def maxsize(self) -> int:
        return self._queue.maxsize
