"""Synthetic / playback board for development without hardware."""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from bci.board.base import BoardInterface, BoardStatus
from bci.board.brainflow_board import BrainFlowBoard

SYNTHETIC_BOARD_ID = -1


class SyntheticBoard(BrainFlowBoard):
    """
    BrainFlow synthetic board — no physical hardware required.

    Generates realistic EEG-like data via BrainFlow's built-in synthetic driver.
    """

    def __init__(
        self,
        n_channels: int = 8,
        sampling_rate: int = 250,
        poll_interval_sec: float = 0.05,
        eeg_channel_indices: Optional[Sequence[int]] = None,
    ) -> None:
        ch_indices = (
            list(eeg_channel_indices)
            if eeg_channel_indices is not None
            else list(range(1, n_channels + 1))
        )
        super().__init__(
            board_id=SYNTHETIC_BOARD_ID,
            serial_number="",
            poll_interval_sec=poll_interval_sec,
            eeg_channel_indices=ch_indices,
        )
        self._n_channels = n_channels
        self._sampling_rate = sampling_rate

    def get_status(self) -> BoardStatus:
        return BoardStatus(
            is_open=self._is_open,
            is_streaming=self._is_streaming,
            board_id=SYNTHETIC_BOARD_ID,
            sampling_rate=self._sampling_rate,
            n_channels=self._n_channels,
        )
