"""Board acquisition — hardware interfaces and data streaming."""

from bci.board.base import BoardInterface, BoardStatus
from bci.board.brainflow_board import BrainFlowBoard
from bci.board.bridge import StreamBridge
from bci.board.stream import DataStream
from bci.board.synthetic import SyntheticBoard

__all__ = [
    "BoardInterface",
    "BoardStatus",
    "BrainFlowBoard",
    "DataStream",
    "StreamBridge",
    "SyntheticBoard",
]
