"""SSVEP flicker stimulus model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class Target:
    """Represents a flickering SSVEP target on screen."""

    position: tuple[float, float]  # Normalized coordinates (x, y) in range [0, 1]
    frequency: float               # Flicker frequency in Hz
    pattern: str                   # Flicker pattern / method, e.g. 'square-wave', 'sine'
    label: str = ""                # Text label of target character


def generate_3x3_grid(
    config: Optional[dict[str, Any]] = None,
) -> list[Target]:
    """
    Generate a 3x3 grid of 9 Target instances from a configuration dictionary.

    If no config is provided, uses default frequencies (8.0 to 16.0 Hz),
    labels ('A' to 'I'), a square-wave pattern, and centered grid positions.
    """
    if config is None:
        config = {}

    # Defaults
    freqs = config.get("frequencies", [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    labels = config.get("labels", ["A", "B", "C", "D", "E", "F", "G", "H", "I"])
    pattern = config.get("flicker_method", "square-wave")

    # If positions are in config, use them, otherwise generate default normalized positions
    positions = config.get("positions")
    if not positions:
        # 3x3 grid centered in normalized [0, 1] space
        positions = [
            (0.2, 0.8), (0.5, 0.8), (0.8, 0.8),  # Row 1 (top)
            (0.2, 0.5), (0.5, 0.5), (0.8, 0.5),  # Row 2 (middle)
            (0.2, 0.2), (0.5, 0.2), (0.8, 0.2),  # Row 3 (bottom)
        ]

    targets: list[Target] = []
    for i in range(min(9, len(freqs))):
        pos = positions[i]
        freq = freqs[i]
        lbl = labels[i] if i < len(labels) else f"T{i+1}"
        targets.append(Target(position=pos, frequency=freq, pattern=pattern, label=lbl))

    return targets
