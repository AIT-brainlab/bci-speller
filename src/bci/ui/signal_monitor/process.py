"""
Child-process entry point for the live EEG matplotlib window.

All matplotlib imports stay inside this function so Windows ``spawn`` does not
reload heavy GUI stacks at import time.
"""

from __future__ import annotations

import multiprocessing.synchronize
import sys
import time
from pathlib import Path
from typing import Any, List, Sequence

# Windows spawn: child process must set up import paths before bci imports.
_src_root = Path(__file__).resolve().parents[3]
_proj_root = _src_root.parent
for _p in (_proj_root, _src_root):
    _entry = str(_p)
    if _entry not in sys.path:  # pragma: no cover
        sys.path.insert(0, _entry)  # pragma: no cover

import numpy as np
from numpy.typing import NDArray

from bci.ui.signal_monitor.widgets import (
    CHANNEL_COLORS,
    GRID_COLOR,
    MARKER_COLOR,
    PANEL_COLOR,
    STATUS_OK,
    STATUS_PAUSE,
    STATUS_STOP,
    TEXT_COLOR,
    apply_plot_theme,
    position_figure_on_monitor,
)

DATA_QUEUE_MAXSIZE = 300
MARKER_QUEUE_MAXSIZE = 100


def run_signal_monitor_process(
    data_q: Any,
    marker_q: Any,
    stop_event: multiprocessing.synchronize.Event,
    pause_event: multiprocessing.synchronize.Event,
    n_channels: int,
    ch_indices: Sequence[int],
    window_sec: float,
    fs: float,
    plot_hz: int,
    amplitude_uv: float,
    labels: Sequence[str],
    monitor_index: int,
) -> None:
    import matplotlib

    matplotlib.use("TkAgg")
    import matplotlib.animation as animation
    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt

    buf_size: int = int(window_sec * fs)
    buffer: NDArray[np.float64] = np.zeros((n_channels, buf_size), dtype=np.float64)
    x_data: NDArray[np.float64] = np.linspace(0, window_sec, buf_size)
    total_samples: int = 0
    last_hz_time: float = time.perf_counter()
    last_hz_count: int = 0
    live_hz: float = 0.0

    apply_plot_theme()

    fig = plt.figure(figsize=(12, 1.1 * n_channels + 1.5))
    try:
        fig.canvas.manager.set_window_title("EEG Real-Time Visualizer")
    except Exception:
        pass

    gs = gridspec.GridSpec(
        n_channels + 1,
        2,
        figure=fig,
        height_ratios=[0.6] + [1.0] * n_channels,
        width_ratios=[20, 1],
        hspace=0.08,
        wspace=0.02,
    )

    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_axis_off()

    status_text = ax_header.text(
        0.01, 0.5, "LIVE",
        transform=ax_header.transAxes,
        fontsize=10, fontweight="bold", va="center", color=STATUS_OK,
    )
    hz_text = ax_header.text(
        0.40, 0.5, f"Recv 0/s (EEG {int(fs)} Hz)",
        transform=ax_header.transAxes, fontsize=9, va="center", color=TEXT_COLOR,
    )
    sample_text = ax_header.text(
        0.60, 0.5, "Samples: 0",
        transform=ax_header.transAxes, fontsize=9, va="center", color=TEXT_COLOR,
    )
    ax_header.text(
        0.99, 0.5, f"Window: {window_sec}s  |  +/-{amplitude_uv} uV",
        transform=ax_header.transAxes, fontsize=9, va="center", ha="right", color=TEXT_COLOR,
    )

    ax_qh = fig.add_subplot(gs[0, 1])
    ax_qh.set_axis_off()
    ax_qh.text(
        0.5, 0.5, "Q",
        transform=ax_qh.transAxes, fontsize=8, ha="center", va="center", color=TEXT_COLOR,
    )

    axes: List[Any] = []
    lines: List[Any] = []
    qlines: List[Any] = []
    ch_indices_list = list(ch_indices)

    for ch in range(n_channels):
        color = CHANNEL_COLORS[ch % len(CHANNEL_COLORS)]
        lbl = labels[ch] if ch < len(labels) else f"CH{ch + 1}"

        ax = fig.add_subplot(gs[ch + 1, 0])
        ax.set_xlim(0, window_sec)
        ax.set_ylim(-amplitude_uv, amplitude_uv)
        ax.set_ylabel(lbl, fontsize=9, rotation=0, labelpad=28, va="center", color=color)
        ax.set_yticks([-amplitude_uv, 0, amplitude_uv])
        ax.set_yticklabels(
            [f"-{int(amplitude_uv)}", "0", f"+{int(amplitude_uv)}"], fontsize=7,
        )
        ax.axhline(0, color=GRID_COLOR, linewidth=0.5, zorder=1)
        ax.grid(True, axis="x", linestyle="--", linewidth=0.3, alpha=0.5)
        ax.set_facecolor(PANEL_COLOR)
        if ch < n_channels - 1:
            ax.tick_params(labelbottom=False)
        else:
            ax.set_xlabel("Time (s)", fontsize=8)

        (line,) = ax.plot(x_data, np.zeros(buf_size), color=color, linewidth=0.8, zorder=2)
        axes.append(ax)
        lines.append(line)

        ax_q = fig.add_subplot(gs[ch + 1, 1])
        ax_q.set_xlim(0, 1)
        ax_q.set_ylim(0, 1)
        ax_q.set_facecolor(PANEL_COLOR)
        ax_q.set_axis_off()
        ax_q.add_patch(plt.Rectangle((0.1, 0.05), 0.8, 0.9, color="#333333", zorder=1))
        (qpatch,) = ax_q.fill(
            [0.1, 0.9, 0.9, 0.1], [0.05, 0.05, 0.95, 0.95],
            color=STATUS_OK, alpha=0.7, zorder=2,
        )
        qlines.append(qpatch)

    fig.subplots_adjust(left=0.06, right=0.98, top=0.96, bottom=0.06, hspace=0.35)

    position_figure_on_monitor(fig, monitor_index)

    def _update(_frame: int) -> List[Any]:
        nonlocal buffer, total_samples, last_hz_time, last_hz_count, live_hz

        if stop_event.is_set():
            try:
                plt.close(fig)
            except Exception:
                pass
            return lines + qlines

        if pause_event.is_set():
            while True:
                try:
                    chunk = data_q.get_nowait()
                    eeg = chunk[ch_indices_list, :]
                    n_new = eeg.shape[1]
                    if n_new >= buf_size:
                        buffer = eeg[:, -buf_size:]
                    else:
                        buffer = np.roll(buffer, -n_new, axis=1)
                        buffer[:, -n_new:] = eeg
                    total_samples += n_new
                    last_hz_count += n_new
                except Exception:
                    break

            now = time.perf_counter()
            elapsed = now - last_hz_time
            if elapsed >= 1.0:  # pragma: no cover
                live_hz = last_hz_count / elapsed  # pragma: no cover
                last_hz_count = 0  # pragma: no cover
                last_hz_time = now  # pragma: no cover

        for ch, line in enumerate(lines):
            line.set_ydata(buffer[ch])

        for ch in range(n_channels):
            rms = float(np.sqrt(np.mean(buffer[ch] ** 2)))
            quality = np.clip(rms / (amplitude_uv * 0.5), 0.0, 1.0)
            if rms < 1.0:
                color = STATUS_STOP
            elif quality > 0.8:  # pragma: no cover
                color = MARKER_COLOR  # pragma: no cover
            elif quality > 0.15:
                color = STATUS_OK
            else:  # pragma: no cover
                color = STATUS_PAUSE  # pragma: no cover
            qlines[ch].set_facecolor(color)

        while True:
            try:
                label = marker_q.get_nowait()
                x_pos = window_sec - 0.05
                for ax in axes:
                    ax.axvline(
                        x_pos, color=MARKER_COLOR, linewidth=1.2,
                        linestyle="--", alpha=0.8, zorder=3,
                    )
                if axes:
                    axes[0].text(  # pragma: no cover
                        x_pos, amplitude_uv * 0.85, label or "M",
                        color=MARKER_COLOR, fontsize=7, ha="right", va="top",
                    )
            except Exception:
                break

        if pause_event.is_set():
            status_text.set_text("LIVE")
            status_text.set_color(STATUS_OK)
        else:
            status_text.set_text("PAUSED")
            status_text.set_color(STATUS_PAUSE)

        hz_text.set_text(f"Recv {live_hz:.0f}/s (EEG {int(fs)} Hz)")
        sample_text.set_text(f"Samples: {total_samples:,}")

        return lines + qlines

    interval_ms = int(1000 / plot_hz)
    _ani = animation.FuncAnimation(
        fig, _update, interval=interval_ms, blit=False, cache_frame_data=False,
    )

    try:
        plt.show()
    except Exception as exc:
        print(f"[SignalMonitorApp] Error in plt.show(): {exc}", flush=True)
    finally:
        print("[SignalMonitorApp] Window closed", flush=True)
