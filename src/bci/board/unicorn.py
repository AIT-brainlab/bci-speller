"""g.tec Unicorn board implementation."""

from __future__ import annotations

from typing import Optional, Sequence

from brainflow.board_shim import BoardIds

from bci.board.base import BoardStatus
from bci.board.brainflow_board import BrainFlowBoard
from bci.board.streaming import POLL_INTERVAL_SEC

UNICORN_BOARD_ID = BoardIds.UNICORN_BOARD.value
UNICORN_SAMPLING_RATE = 250
UNICORN_CHANNEL_NAMES = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8"]


class UnicornBoard(BrainFlowBoard):
    """g.tec Unicorn EEG board — 8 channels at 250 Hz."""

    def __init__(
        self,
        serial_number: str = "",
        poll_interval_sec: float = POLL_INTERVAL_SEC,
        eeg_channel_indices: Optional[Sequence[int]] = None,
    ) -> None:
        super().__init__(
            board_id=UNICORN_BOARD_ID,
            serial_number=serial_number,
            poll_interval_sec=poll_interval_sec,
            eeg_channel_indices=eeg_channel_indices,
        )

    @property
    def channel_names(self) -> list[str]:
        return list(UNICORN_CHANNEL_NAMES)

    def get_status(self) -> BoardStatus:
        return BoardStatus(
            is_open=self._is_open,
            is_streaming=self._is_streaming,
            board_id=UNICORN_BOARD_ID,
            sampling_rate=UNICORN_SAMPLING_RATE,
            n_channels=len(UNICORN_CHANNEL_NAMES),
        )
