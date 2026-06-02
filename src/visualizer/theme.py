"""Visual theme constants for the matplotlib EEG plot."""

from typing import Final, Sequence

CHANNEL_LABELS: Final[Sequence[str]] = (
    "Fz",
    "C3",
    "Cz",
    "C4",
    "Pz",
    "PO7",
    "Oz",
    "PO8",
)

CHANNEL_COLORS: Final[Sequence[str]] = (
    "#378ADD",
    "#1D9E75",
    "#D85A30",
    "#D4537E",
    "#7F77DD",
    "#BA7517",
    "#639922",
    "#888780",
)

BG_COLOR: Final[str] = "#1a1a1a"
PANEL_COLOR: Final[str] = "#222222"
TEXT_COLOR: Final[str] = "#c8c8c8"
GRID_COLOR: Final[str] = "#333333"
MARKER_COLOR: Final[str] = "#ff4444"
STATUS_OK: Final[str] = "#1D9E75"
STATUS_PAUSE: Final[str] = "#BA7517"
STATUS_STOP: Final[str] = "#888780"
