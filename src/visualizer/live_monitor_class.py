"""
EEGVisualizer — live EEG plot in a dedicated OS process.

Delegates to ``bci.ui.signal_monitor.SignalMonitorApp`` while keeping the
original API used by ``experiment.py`` and ``standalone.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, Sequence

# Ensure the refactored bci package is importable from the visualizer tree.
_BCI_SRC = Path(__file__).resolve().parent.parent
if str(_BCI_SRC) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_BCI_SRC))  # pragma: no cover

from bci.ui.signal_monitor import SignalMonitorApp


class EEGVisualizer:
    """Separate OS process for live EEG plot (dual-monitor dev view)."""

    def __init__(
        self,
        board_shim: Any,
        board_id: int,
        n_channels: int = 8,
        window_sec: Optional[float] = None,
        plot_hz: Optional[int] = None,
        amplitude_uv: Optional[float] = None,
        channel_labels: Optional[Sequence[str]] = None,
        fs: Optional[int] = None,
        monitor_index: int = 1,
        ch_indices: Optional[Sequence[int]] = None,
    ) -> None:
        self._app = SignalMonitorApp(
            board_id=board_id,
            n_channels=n_channels,
            window_sec=window_sec,
            plot_hz=plot_hz,
            amplitude_uv=amplitude_uv,
            channel_labels=channel_labels,
            fs=fs,
            monitor_index=monitor_index,
            ch_indices=ch_indices,
        )
        self._board_shim = board_shim
        self._board_id = board_id

    @property
    def data_queue(self) -> Any:
        return self._app.data_queue

    def start(self) -> None:
        self._app.start()

    def stop(self) -> None:
        self._app.stop()

    def pause(self) -> None:
        self._app.pause()

    def resume(self) -> None:
        self._app.resume()

    def mark(self, label: str = "") -> None:
        self._app.mark(label)

    @property
    def is_running(self) -> bool:
        return self._app.is_running

    # Exposed for unit tests that inspect process arguments.
    @property
    def _proc_args(self) -> tuple:
        return self._app._proc_args

    @property
    def _pause_event(self) -> Any:
        return self._app._pause_event

    @property
    def _marker_queue(self) -> Any:
        return self._app._marker_queue

    @_marker_queue.setter
    def _marker_queue(self, value: Any) -> None:
        self._app._marker_queue = value

    @property
    def _process(self) -> Any:
        return self._app._process

    @_process.setter
    def _process(self, value: Any) -> None:
        self._app._process = value
