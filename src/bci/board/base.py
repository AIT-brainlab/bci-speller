"""Abstract board interface for EEG acquisition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from bci.board.stream import DataStream


@dataclass(frozen=True)
class BoardStatus:
    """Snapshot of board connection and streaming state."""

    is_open: bool
    is_streaming: bool
    board_id: Optional[int] = None
    sampling_rate: Optional[int] = None
    n_channels: Optional[int] = None


class BoardInterface(ABC):
    """Contract for opening a board, streaming samples, and exposing a raw queue."""

    def __init__(self) -> None:
        self.raw_stream = DataStream()
        self._subscribers: list[DataStream] = [self.raw_stream]

    def get_raw_stream(self) -> DataStream:
        """Return the raw DataStream object."""
        return self.raw_stream

    def add_subscriber(self, stream: DataStream) -> None:
        """Register a new DataStream subscriber to receive sample chunks."""
        if stream not in self._subscribers:
            self._subscribers.append(stream)

    def remove_subscriber(self, stream: DataStream) -> None:
        """Unregister a DataStream subscriber."""
        if stream in self._subscribers:
            self._subscribers.remove(stream)

    @abstractmethod
    def open(self) -> None:
        """Prepare the board session."""

    @abstractmethod
    def close(self) -> None:
        """Stop streaming and release the board session."""

    @abstractmethod
    def get_status(self) -> BoardStatus:
        """Return current connection and streaming state."""

    @abstractmethod
    def start_stream(self) -> None:
        """Begin pushing sample chunks onto ``raw_stream``."""

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop the streaming loop."""

    @abstractmethod
    def get_buffer(self) -> NDArray[np.float64]:
        """Return accumulated board data (BrainFlow ``get_board_data`` semantics)."""

    @abstractmethod
    def insert_marker(self, marker: float) -> None:
        """Insert a marker into the board data stream."""

    @property
    def eeg_channel_indices(self) -> Sequence[int]:
        """Row indices for EEG channels in board data arrays."""
        return tuple(range(1, 9))  # pragma: no cover
