"""Theme constants are well-formed."""

from __future__ import annotations

from visualizer.theme import CHANNEL_COLORS, CHANNEL_LABELS


def test_channel_lists_match_length() -> None:
    assert len(CHANNEL_LABELS) == 8
    assert len(CHANNEL_COLORS) >= 8
