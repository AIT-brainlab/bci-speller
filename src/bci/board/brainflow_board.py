"""BrainFlow hardware board implementing BoardInterface."""

from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from bci.board.base import BoardInterface, BoardStatus
from bci.board.stream import DEFAULT_STREAM_MAXSIZE, DataStream
from bci.board.streaming import POLL_INTERVAL_SEC, BoardStreamLoop


class BrainFlowBoard(BoardInterface):
    """Wraps a BrainFlow BoardShim with a background streaming loop."""

    def __init__(
        self,
        board_id: int,
        serial_number: str = "",
        poll_interval_sec: float = POLL_INTERVAL_SEC,
        stream_maxsize: int = DEFAULT_STREAM_MAXSIZE,
        eeg_channel_indices: Optional[Sequence[int]] = None,
    ) -> None:
        from brainflow.board_shim import BoardShim, BrainFlowInputParams

        super().__init__()
        self.raw_stream = DataStream(maxsize=stream_maxsize)
        # super().__init__() seeded _subscribers with the OLD raw_stream reference.
        # Re-sync it so _broadcast_chunk writes to the correct queue.
        self._subscribers = [self.raw_stream]
        self._board_id = int(board_id)
        params = BrainFlowInputParams()
        if serial_number:
            params.serial_number = serial_number
        self._board_shim: Any = BoardShim(self._board_id, params)
        self._poll_interval_sec = float(poll_interval_sec)
        self._stream_loop: Optional[BoardStreamLoop] = None
        self._is_open = False
        self._is_streaming = False
        self._eeg_channel_indices = (
            list(eeg_channel_indices)
            if eeg_channel_indices is not None
            else list(BoardShim.get_eeg_channels(self._board_id))
        )

    @property
    def eeg_channel_indices(self) -> Sequence[int]:
        return tuple(self._eeg_channel_indices)

    def open(self) -> None:
        self._board_shim.prepare_session()
        self._is_open = True

    def close(self) -> None:
        if self._is_streaming:
            self.stop_stream()  # pragma: no cover
        if self._is_open:
            try:
                if self._board_shim.is_prepared():
                    self._board_shim.release_session()
            except Exception:  # pragma: no cover
                pass  # pragma: no cover
            self._is_open = False

    def get_status(self) -> BoardStatus:
        from brainflow.board_shim import BoardShim

        fs: Optional[int] = None
        try:
            fs = int(BoardShim.get_sampling_rate(self._board_id))
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
        return BoardStatus(
            is_open=self._is_open,
            is_streaming=self._is_streaming,
            board_id=self._board_id,
            sampling_rate=fs,
            n_channels=len(self._eeg_channel_indices),
        )

    def _broadcast_chunk(self, chunk: NDArray[np.float64]) -> None:
        """Forward a chunk to all registered subscribers."""
        for sub in self._subscribers:
            try:
                sub.put_nowait(chunk)
            except Exception:  # pragma: no cover
                pass  # pragma: no cover

    def start_stream(self) -> None:
        if self._is_streaming:
            return  # pragma: no cover
        self._board_shim.start_stream()
        self._board_shim.get_board_data()
        self._stream_loop = BoardStreamLoop(
            poll_buffer=self.get_buffer,
            put_chunk=self._broadcast_chunk,
            poll_interval_sec=self._poll_interval_sec,
        )
        self._stream_loop.start()
        self._is_streaming = True

    def stop_stream(self) -> None:
        if self._stream_loop is not None:
            self._stream_loop.stop()
            self._stream_loop = None
        if self._is_open:
            try:
                self._board_shim.stop_stream()
            except Exception:  # pragma: no cover
                pass  # pragma: no cover
        self._is_streaming = False

    def get_buffer(self) -> NDArray[np.float64]:
        data = self._board_shim.get_board_data()
        if data is None:
            return np.empty((0, 0), dtype=np.float64)
        return np.asarray(data, dtype=np.float64)

    def insert_marker(self, marker: float) -> None:  # pragma: no cover
        if self._is_open:  # pragma: no cover
            self._board_shim.insert_marker(marker)  # pragma: no cover
