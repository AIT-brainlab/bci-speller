"""SSVEP flicker stimulus model."""

from __future__ import annotations

from typing import Any, Optional, Sequence


class Target:
    """Represents a flickering SSVEP target on screen."""

    def __init__(
        self,
        position: tuple[float, float],
        frequency: float,
        pattern: str,
        label: str = "",
        win: Optional[Any] = None,
        width: float = 100.0,
        height: float = 100.0,
        color_off: str = "#333333",
        text_color: str = "#FFFFFF",
    ) -> None:
        self.position = position
        self.frequency = frequency
        self.pattern = pattern
        self.label = label
        self.width = width
        self.height = height
        self.color_off = color_off
        self.text_color = text_color

        self.rect: Optional[Any] = None
        self.text: Optional[Any] = None

        if win is not None:  # pragma: no cover
            self.init_visuals(win)

    def init_visuals(self, win: Any) -> None:
        from psychopy import visual

        self.rect = visual.Rect(
            win,
            width=self.width,
            height=self.height,
            pos=self.position,
            fillColor=self.color_off,
            lineColor="#555555",
            lineWidth=1,
        )
        self.text = visual.TextStim(
            win,
            text=self.label,
            pos=self.position,
            color=self.text_color,
            height=35.0,  # Match speller config character height
            bold=True,
            font="DejaVu Sans",
        )

    def draw(self) -> None:
        if self.rect is not None:
            self.rect.draw()
        if self.text is not None:
            self.text.draw()


def generate_3x3_grid(
    config: Optional[dict[str, Any]] = None,
    win: Optional[Any] = None,
) -> list[Target]:
    """
    Generate a 3x3 grid of 9 Target instances from a configuration dictionary.

    If no config is provided, uses default frequencies (8.0 to 9.6 Hz),
    labels ('A' to 'I'), a square-wave pattern, and default pixel grid positions.
    """
    if config is None:
        config = {}

    # Defaults
    freqs = config.get("frequencies", [8.0, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4, 9.6])
    labels = config.get("labels", ["A", "B", "C", "D", "E", "F", "G", "H", "I"])
    pattern = config.get("flicker_method", "square-wave")

    # Grid parameters
    width = float(config.get("target_width_pixels", 100.0))
    height = float(config.get("target_height_pixels", 100.0))
    color_off = config.get("color_off", "#333333")
    text_color = config.get("text_color", "#FFFFFF")

    # If positions are in config, use them, otherwise generate default coordinates
    positions = config.get("positions")
    if not positions:
        # Default positions in screen pixel units for PsychoPy center-anchored coordinates
        positions = [
            (-800, 300), (0, 300), (800, 300),      # Row 1 (top)
            (-800, 0),   (0, 0),   (800, 0),        # Row 2 (middle)
            (-800, -300), (0, -300), (800, -300),   # Row 3 (bottom)
        ]

    targets: list[Target] = []
    for i in range(min(9, len(freqs))):
        pos = positions[i]
        freq = freqs[i]
        lbl = labels[i] if i < len(labels) else f"T{i+1}"
        targets.append(
            Target(
                position=pos,
                frequency=freq,
                pattern=pattern,
                label=lbl,
                win=win,
                width=width,
                height=height,
                color_off=color_off,
                text_color=text_color,
            )
        )

    return targets
