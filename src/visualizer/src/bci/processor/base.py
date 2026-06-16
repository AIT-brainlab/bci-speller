"""Abstract processor interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProcessorInterface(ABC):
    """Transform a single data chunk in a processing pipeline."""

    @abstractmethod
    def process(self, chunk: Any) -> Any:
        """Return the processed chunk."""
