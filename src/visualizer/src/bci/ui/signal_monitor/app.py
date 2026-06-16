"""
Live EEG signal monitor — separate OS process for the matplotlib window.

Compatible with the original ``EEGVisualizer`` API:
``data_queue`` accepts chunks from ``BoardStreamFeeder`` or
``EEGStreamController.add_subscriber()``.

When a ``board`` is supplied, a background bridge forwards
``board.raw_stream`` into ``data_queue`` automatically.
"""

from __future__ import annotations

import multiprocessing
import sys
import time
from multiprocessing import Process
from multiprocessing.queues import Queue as MpQueue
from typing import Any, List, Optional, Sequence

from bci.board.base import BoardInterface
from bci.board.bridge import StreamBridge
from bci.ui.signal_monitor.process import (
    MARKER_QUEUE_MAXSIZE,
    run_signal_monitor_process,
)
from bci.ui.signal_monitor.widgets import CHANNEL_LABELS


def _resolve_plot_params(
    window_sec: Optional[float],
    plot_hz: Optional[int],
    amplitude_uv: Optional[float],
) -> tuple[float, int, float]:
    try:
        from visualizer.config.settings import resolve_plot_params

        return resolve_plot_params(window_sec, plot_hz, amplitude_uv)
    except Exception:
        return (
            float(window_sec if window_sec is not None else 5.0),
            int(plot_hz if plot_hz is not None else 20),
            float(amplitude_uv if amplitude_uv is not None else 100.0),
        )


class SignalMonitorApp:
    """Separate OS process for live EEG plot (dual-monitor dev view)."""

    def __init__(
        self,
        board: Optional[BoardInterface] = None,
        board_id: Optional[int] = None,
        n_channels: int = 8,
        window_sec: Optional[float] = None,
        plot_hz: Optional[int] = None,
        amplitude_uv: Optional[float] = None,
        channel_labels: Optional[Sequence[str]] = None,
        fs: Optional[int] = None,
        monitor_index: int = 1,
        ch_indices: Optional[Sequence[int]] = None,
    ) -> None:
        from brainflow.board_shim import BoardShim

        if board is not None:
            status = board.get_status()
            if board_id is None:
                board_id = status.board_id
            if fs is None and status.sampling_rate is not None:
                fs = int(status.sampling_rate)

        if board_id is None:
            board_id = 8

        resolved_window, resolved_plot_hz, resolved_amplitude = _resolve_plot_params(
            window_sec=window_sec,
            plot_hz=plot_hz,
            amplitude_uv=amplitude_uv,
        )

        if fs is None:
            try:
                fs = int(BoardShim.get_sampling_rate(board_id))
            except Exception:
                fs = 250

        if ch_indices is None:
            if board is not None:
                ch_indices = list(board.eeg_channel_indices)[:n_channels]
            else:
                try:
                    eeg_ch = BoardShim.get_eeg_channels(board_id)
                    ch_indices = list(eeg_ch[:n_channels])
                except Exception:
                    ch_indices = list(range(1, n_channels + 1))
        else:
            ch_indices = list(ch_indices)

        labels: List[str] = list(channel_labels or CHANNEL_LABELS)[:n_channels]

        self._data_queue: MpQueue[Any] = multiprocessing.Queue(maxsize=300)
        self._marker_queue: MpQueue[Any] = multiprocessing.Queue(
            maxsize=MARKER_QUEUE_MAXSIZE,
        )
        self._stop_event = multiprocessing.Event()
        self._pause_event = multiprocessing.Event()
        self._pause_event.set()

        self._proc_args = (
            self._data_queue,
            self._marker_queue,
            self._stop_event,
            self._pause_event,
            n_channels,
            ch_indices,
            float(resolved_window),
            float(fs),
            int(resolved_plot_hz),
            float(resolved_amplitude),
            labels,
            int(monitor_index),
        )

        self._process: Optional[Process] = None
        self._board = board
        self._bridge: Optional[StreamBridge] = None
        if board is not None:
            self._bridge = StreamBridge(board.raw_stream, self._data_queue)

    @property
    def data_queue(self) -> MpQueue[Any]:
        """Multiprocessing queue for external producers (feeder / EEGStreamController)."""
        return self._data_queue

    def start(self) -> None:
        self._stop_event.clear()
        self._pause_event.set()
        if self._bridge is not None:
            self._bridge.start()
        self._process = Process(
            target=run_signal_monitor_process,
            args=self._proc_args,
            daemon=False,
            name="SignalMonitorProc",
        )
        self._process.start()
        # Brief wait — catch immediate child crash (common on Windows import errors).
        time.sleep(0.3)
        if self._process.exitcode is not None:
            print(
                f"[SignalMonitorApp] ERROR: plot process exited immediately "
                f"(code={self._process.exitcode})",
                file=sys.stderr,
            )
        else:
            print("[SignalMonitorApp] Started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._bridge is not None:
            self._bridge.stop()
        if self._process and self._process.is_alive():
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
        print("[SignalMonitorApp] Stopped")

    def pause(self) -> None:
        self._pause_event.clear()
        print("[SignalMonitorApp] Paused")

    def resume(self) -> None:
        self._pause_event.set()
        print("[SignalMonitorApp] Resumed")

    def mark(self, label: str = "") -> None:
        try:
            self._marker_queue.put_nowait(label)
        except Exception:
            pass

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.is_alive()
