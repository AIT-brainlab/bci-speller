"""BCI package — board acquisition, processing, recording, and UI."""

from bci.board.base import BoardInterface, BoardStatus
from bci.board.stream import DataStream

__all__ = [
    "BoardInterface",
    "BoardStatus",
    "DataStream",
]
