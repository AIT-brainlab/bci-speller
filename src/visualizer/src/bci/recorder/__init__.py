"""Data recording backends."""

from bci.recorder.base import RecorderInterface
from bci.recorder.fif import FifRecorder

__all__ = [
    "RecorderInterface",
    "FifRecorder",
]
