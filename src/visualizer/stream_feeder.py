"""Push BrainFlow board samples into the visualizer multiprocessing queue."""

from __future__ import annotations

import threading
import time
from typing import Any, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from visualizer.config.constants import (
    AFTER_TIMEOUT,
    DATA_QUEUE_MAXSIZE,
    FEEDER_TIMEOUT,
    POLL_INTERVAL_SEC,
)


class BoardStreamFeeder:
    """
    Background thread: poll ``board_shim.get_board_data()`` and forward copies
    to the visualizer ``data_queue`` (same contract as EEGStreamController).
    """

    def __init__(
        self,
        board_shim: Any,
        data_queue: Any,
        poll_interval_sec: float = POLL_INTERVAL_SEC,
        eeg_row_indices: Optional[Sequence[int]] = None,
    ) -> None:
        self._board_shim = board_shim
        self._data_queue = data_queue
        self._poll_interval_sec = float(poll_interval_sec)
        self._eeg_row_indices = list(eeg_row_indices) if eeg_row_indices else None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the stream feeder thread.

        Initializes the board shim and starts the background polling thread.
        """
        self._board_shim.get_board_data()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="BoardStreamFeeder",
            daemon=True,
        )
        self._thread.start()
        print("[BoardStreamFeeder] Started")

    def stop(self) -> None:
        """Stop the stream feeder thread.

        Signals the thread to stop and waits for it to terminate.
        """
        self._stop_event.set()
        self._pause_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        print("[BoardStreamFeeder] Stopped")

    def pause(self) -> None:
        """Pause the stream feeder.

        Stops polling data from the board.
        """
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume the stream feeder.

        Restarts polling data from the board.
        """
        _ = self._board_shim.get_board_data()
        self._pause_event.set()

    def _loop(self) -> None:
        """Main polling loop.

        Continuously polls the board for data and forwards it to the queue.
        """
        while not self._stop_event.is_set():
            self._pause_event.wait(timeout=self._poll_interval_sec)
            if self._stop_event.is_set():
                break
            if not self._pause_event.is_set():
                continue
            data: NDArray[np.float64] = self._board_shim.get_board_data()
            if data is None or data.size == 0 or data.shape[1] == 0:
                time.sleep(self._poll_interval_sec)
                continue
            try:
                self._data_queue.put_nowait(data.copy())
            except Exception:
                # Queue is full, skip this sample and continue polling
                # The pause event wait above already provides the polling delay
                pass
