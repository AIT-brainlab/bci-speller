"""Tests for monitor placement helper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from visualizer.monitor import position_figure_on_monitor


def test_position_no_window() -> None:
    fig = MagicMock()
    fig.canvas.manager.window = None
    fig.canvas.get_tk_widget.side_effect = RuntimeError("no tk")
    position_figure_on_monitor(fig, 0)


def test_position_with_mock_tk() -> None:
    root = MagicMock()
    fig = MagicMock()
    fig.canvas.manager.window = root
    position_figure_on_monitor(fig, 0)
    root.geometry.assert_called_once()


def test_position_via_tk_widget_no_monitors() -> None:
    """Tk fallback path; geometry skipped when monitor enumeration is empty."""
    root = MagicMock()
    fig = MagicMock()
    fig.canvas.manager.window = None
    widget = MagicMock()
    widget.winfo_toplevel.return_value = root
    fig.canvas.get_tk_widget.return_value = widget
    position_figure_on_monitor(fig, 0)
