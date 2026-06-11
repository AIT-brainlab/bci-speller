"""Full branch coverage for monitor helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from visualizer.monitor import (
    _place_root_on_monitor,
    _resolve_tk_root,
    list_monitors,
    position_figure_on_monitor,
)


def test_resolve_tk_root_manager_fails_tk_fails() -> None:
    fig = MagicMock()
    type(fig.canvas.manager).window = PropertyMock(side_effect=RuntimeError("no manager"))
    fig.canvas.get_tk_widget.side_effect = RuntimeError("no tk")
    assert _resolve_tk_root(fig) is None


def test_resolve_tk_root_from_tk_widget() -> None:
    root = MagicMock()
    fig = MagicMock()
    type(fig.canvas.manager).window = PropertyMock(side_effect=RuntimeError("no manager"))
    widget = MagicMock()
    widget.winfo_toplevel.return_value = root
    fig.canvas.get_tk_widget.return_value = widget
    assert _resolve_tk_root(fig) is root


def test_resolve_tk_root_from_manager() -> None:
    root = MagicMock()
    fig = MagicMock()
    fig.canvas.manager.window = root
    assert _resolve_tk_root(fig) is root


def test_list_monitors_handles_win32_errors() -> None:
    with patch("ctypes.windll") as windll:
        windll.user32.EnumDisplayMonitors.side_effect = RuntimeError("no displays")
        assert list_monitors() == []


def test_place_root_geometry_and_errors() -> None:
    root = MagicMock()
    _place_root_on_monitor(root, [(0, 0, 1920, 1080)], 0)
    root.geometry.assert_called_once()

    root.geometry.side_effect = RuntimeError("broken")
    _place_root_on_monitor(root, [(0, 0, 800, 600)], 0)


def test_place_root_empty_monitors() -> None:
    root = MagicMock()
    _place_root_on_monitor(root, [], 0)
    root.geometry.assert_not_called()


def test_position_figure_end_to_end() -> None:
    root = MagicMock()
    fig = MagicMock()
    fig.canvas.manager.window = root
    with patch("visualizer.monitor.list_monitors", return_value=[(0, 0, 1600, 900)]):
        position_figure_on_monitor(fig, 0)
    root.geometry.assert_called_once()

