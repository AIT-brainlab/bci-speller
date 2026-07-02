"""Board acquisition — hardware interfaces and data streaming."""

from bci.board.synthetic import SyntheticBoard
from bci.board.unicorn import UnicornBoard

__all__ = [
    "SyntheticBoard",
    "UnicornBoard",
]
