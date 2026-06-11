"""
EEGVisualizer — live EEG plot in a dedicated OS process.

Use with EEGStreamController.add_subscriber(visualizer.data_queue), or run
standalone via ``python -m visualizer``.
"""

from __future__ import annotations

import multiprocessing
from multiprocessing import Process
from multiprocessing.queues import Queue as MpQueue
from typing import Any, List, Optional, Sequence

from visualizer.config.settings import resolve_plot_params
from visualizer.process import run_visualizer_process
from visualizer.theme import CHANNEL_LABELS


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
        from brainflow.board_shim import BoardShim

        resolved_window, resolved_plot_hz, resolved_amplitude = resolve_plot_params(
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
            try:
                eeg_ch = BoardShim.get_eeg_channels(board_id)
                ch_indices = list(eeg_ch[:n_channels])
            except Exception:
                ch_indices = list(range(1, n_channels + 1))
        else:
            ch_indices = list(ch_indices)

        labels: List[str] = list(channel_labels or CHANNEL_LABELS)[:n_channels]

        self._data_queue: MpQueue[Any] = multiprocessing.Queue(maxsize=300)
        self._marker_queue: MpQueue[Any] = multiprocessing.Queue(maxsize=100)
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
        self._board_shim = board_shim
        self._board_id = board_id

    @property
    def data_queue(self) -> MpQueue[Any]:
        return self._data_queue

    def start(self) -> None:
        self._stop_event.clear()
        self._pause_event.set()
        self._process = Process(
            target=run_visualizer_process,
            args=self._proc_args,
            daemon=False,
            name="EEGVisualizerProc",
        )
        self._process.start()
        print("[EEGVisualizer] Started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._process and self._process.is_alive():
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
        print("[EEGVisualizer] Stopped")

    def pause(self) -> None:
        self._pause_event.clear()
        print("[EEGVisualizer] Paused")

    def resume(self) -> None:
        self._pause_event.set()
        print("[EEGVisualizer] Resumed")

    def mark(self, label: str = "") -> None:
        try:
            self._marker_queue.put_nowait(label)
        except Exception:
            pass

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.is_alive()
