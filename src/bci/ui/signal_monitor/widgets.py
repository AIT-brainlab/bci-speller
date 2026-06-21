"""Matplotlib widgets, theme, and monitor placement for the signal monitor."""

from __future__ import annotations

from typing import Any, Final, List, Sequence, Tuple

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

GEOMETRY_MARGIN: Final[int] = 48


def list_monitors() -> List[Tuple[int, int, int, int]]:
    """Return ``(x, y, width, height)`` for each display. Empty if enumeration fails."""
    monitors: List[Tuple[int, int, int, int]] = []
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        def _callback(hmonitor: int, hdc: int, lprect: Any, _data: float) -> bool:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
            r = info.rcMonitor
            monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
            return True

        enum_proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(RECT),
            ctypes.c_double,
        )(_callback)
        ctypes.windll.user32.EnumDisplayMonitors(0, 0, enum_proc, 0)
    except Exception:
        pass
    return monitors


def _resolve_tk_root(fig: Any) -> Any | None:
    try:
        return fig.canvas.manager.window
    except Exception:
        try:
            return fig.canvas.get_tk_widget().winfo_toplevel()
        except Exception:
            return None


def _place_root_on_monitor(
    root: Any,
    monitors: List[Tuple[int, int, int, int]],
    monitor_index: int,
) -> None:
    if not monitors:
        return
    idx = min(max(int(monitor_index), 0), len(monitors) - 1)
    x, y, w, h = monitors[idx]
    margin = GEOMETRY_MARGIN
    geo_w = max(900, w - margin)
    geo_h = max(650, h - margin)
    geo_x = x + max(0, (w - geo_w) // 2)
    geo_y = y + max(0, (h - geo_h) // 2)
    try:
        root.geometry(f"{geo_w}x{geo_h}+{geo_x}+{geo_y}")
        root.attributes("-topmost", True)
        root.after(800, lambda: root.attributes("-topmost", False))
        root.lift()
        root.focus_force()
    except Exception:
        pass


def position_figure_on_monitor(fig: Any, monitor_index: int = 1) -> None:
    """Place the Tk/matplotlib window on a specific monitor (0 = primary)."""
    root = _resolve_tk_root(fig)
    if root is None:
        return
    _place_root_on_monitor(root, list_monitors(), monitor_index)


def apply_plot_theme() -> None:
    """Set matplotlib rcParams for the dark EEG monitor theme."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.facecolor": BG_COLOR,
            "axes.facecolor": PANEL_COLOR,
            "axes.edgecolor": GRID_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "xtick.color": TEXT_COLOR,
            "ytick.color": TEXT_COLOR,
            "text.color": TEXT_COLOR,
            "grid.color": GRID_COLOR,
            "grid.linewidth": 0.4,
            "font.size": 9,
            "font.family": "DejaVu Sans",
        }
    )
