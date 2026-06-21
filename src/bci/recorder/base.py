"""Abstract recorder interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RecorderInterface(ABC):
    """Persist streamed chunks to disk or another sink."""

    @abstractmethod
    def start(self) -> None:
        """Begin recording."""

    @abstractmethod
    def stop(self) -> None:
        """Stop recording and flush resources."""

    @abstractmethod
    def write(self, chunk: Any) -> None:
        """Append one data chunk."""
