"""
eeg_visualizer.py  –  Live EEG visualizer in a dedicated OS process.

Architecture fix
----------------
BEFORE: ran in a threading.Thread and called board_shim.get_board_data()
        → competed with EEGStreamController for the same buffer
        → plt.show() failed because PsychoPy owns the main thread

AFTER:  runs in a multiprocessing.Process (own window, own main thread)
        → never calls get_board_data(); reads only from data_queue
        → EEGStreamController.add_subscriber(visualizer.data_queue) wires it

All matplotlib imports are INSIDE _run_visualizer_process() so the Windows
'spawn' start method does not re-execute PsychoPy/BrainFlow on module import.
"""

import multiprocessing
import numpy as np
import time

# ── constants ─────────────────────────────────────────────────────────────────
WINDOW_SEC   = 5
PLOT_HZ      = 20
AMPLITUDE_UV = 100

CHANNEL_LABELS = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8"]  #########
CHANNEL_COLORS = [
    "#378ADD", "#1D9E75", "#D85A30", "#D4537E",
    "#7F77DD", "#BA7517", "#639922", "#888780",
]

BG_COLOR     = "#1a1a1a"
PANEL_COLOR  = "#222222"
TEXT_COLOR   = "#c8c8c8"
GRID_COLOR   = "#333333"
MARKER_COLOR = "#ff4444"
STATUS_OK    = "#1D9E75"
STATUS_PAUSE = "#BA7517"
STATUS_STOP  = "#888780"


def _position_figure_on_monitor(fig, monitor_index=1):
    """Place the Tk/matplotlib window on a specific monitor (0 = primary)."""
    try:
        root = fig.canvas.manager.window
    except Exception:
        try:
            root = fig.canvas.get_tk_widget().winfo_toplevel()
        except Exception:
            return

    monitors = []
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

        def _callback(hmonitor, hdc, lprect, _data):
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

    if not monitors:
        return

    idx = min(max(int(monitor_index), 0), len(monitors) - 1)
    x, y, w, h = monitors[idx]
    margin = 48
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


# ── child-process entry point ────────────────────────────────────────────────

def _run_visualizer_process(
    data_q,
    marker_q,
    stop_event,
    pause_event,
    n_channels,
    ch_indices,
    window_sec,
    fs,
    plot_hz,
    amplitude_uv,
    labels,
    monitor_index,
):
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.animation as animation

    buf_size      = int(window_sec * fs)
    buffer        = np.zeros((n_channels, buf_size))
    x_data        = np.linspace(0, window_sec, buf_size)
    total_samples = 0
    last_hz_time  = time.perf_counter()
    last_hz_count = 0
    live_hz       = 0.0

    plt.rcParams.update({
        "figure.facecolor": BG_COLOR,
        "axes.facecolor":   PANEL_COLOR,
        "axes.edgecolor":   GRID_COLOR,
        "axes.labelcolor":  TEXT_COLOR,
        "xtick.color":      TEXT_COLOR,
        "ytick.color":      TEXT_COLOR,
        "text.color":       TEXT_COLOR,
        "grid.color":       GRID_COLOR,
        "grid.linewidth":   0.4,
        "font.size":        9,
        "font.family":      "DejaVu Sans",
    })

    fig = plt.figure(figsize=(12, 1.1 * n_channels + 1.5))
    try:
        fig.canvas.manager.set_window_title("EEG Real-Time Visualizer")
    except Exception:
        pass

    gs = gridspec.GridSpec(
        n_channels + 1, 2,
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
        fontsize=10, fontweight="bold",
        va="center", color=STATUS_OK,
    )
    hz_text = ax_header.text(
        0.40, 0.5, f"Recv 0/s (EEG {int(fs)} Hz)",
        transform=ax_header.transAxes,
        fontsize=9, va="center", color=TEXT_COLOR,
    )
    sample_text = ax_header.text(
        0.60, 0.5, "Samples: 0",
        transform=ax_header.transAxes,
        fontsize=9, va="center", color=TEXT_COLOR,
    )
    ax_header.text(
        0.99, 0.5, f"Window: {window_sec}s  |  +/-{amplitude_uv} uV",
        transform=ax_header.transAxes,
        fontsize=9, va="center", ha="right", color=TEXT_COLOR,
    )

    ax_qh = fig.add_subplot(gs[0, 1])
    ax_qh.set_axis_off()
    ax_qh.text(0.5, 0.5, "Q", transform=ax_qh.transAxes,
               fontsize=8, ha="center", va="center", color=TEXT_COLOR)

    axes, lines, qlines = [], [], []
    for ch in range(n_channels):
        color = CHANNEL_COLORS[ch % len(CHANNEL_COLORS)]
        lbl   = labels[ch] if ch < len(labels) else f"CH{ch+1}"

        ax = fig.add_subplot(gs[ch + 1, 0])
        ax.set_xlim(0, window_sec)
        ax.set_ylim(-amplitude_uv, amplitude_uv)
        ax.set_ylabel(lbl, fontsize=9, rotation=0,
                      labelpad=28, va="center", color=color)
        ax.set_yticks([-amplitude_uv, 0, amplitude_uv])
        ax.set_yticklabels(
            [f"-{int(amplitude_uv)}", "0", f"+{int(amplitude_uv)}"],
            fontsize=7,
        )
        ax.axhline(0, color=GRID_COLOR, linewidth=0.5, zorder=1)
        ax.grid(True, axis="x", linestyle="--", linewidth=0.3, alpha=0.5)
        ax.set_facecolor(PANEL_COLOR)
        if ch < n_channels - 1:
            ax.tick_params(labelbottom=False)
        else:
            ax.set_xlabel("Time (s)", fontsize=8)

        (line,) = ax.plot(x_data, np.zeros(buf_size),
                          color=color, linewidth=0.8, zorder=2)
        axes.append(ax)
        lines.append(line)

        ax_q = fig.add_subplot(gs[ch + 1, 1])
        ax_q.set_xlim(0, 1)
        ax_q.set_ylim(0, 1)
        ax_q.set_facecolor(PANEL_COLOR)
        ax_q.set_axis_off()
        ax_q.add_patch(plt.Rectangle((0.1, 0.05), 0.8, 0.9,
                                      color="#333333", zorder=1))
        (qpatch,) = ax_q.fill(
            [0.1, 0.9, 0.9, 0.1],
            [0.05, 0.05, 0.95, 0.95],
            color=STATUS_OK, alpha=0.7, zorder=2,
        )
        qlines.append(qpatch)

    try:
        fig.tight_layout(rect=[0, 0, 1, 1])
    except Exception:
        pass

    _position_figure_on_monitor(fig, monitor_index)

    def _update(frame):
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
                    eeg   = chunk[ch_indices, :]
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

            now     = time.perf_counter()
            elapsed = now - last_hz_time
            if elapsed >= 1.0:
                live_hz       = last_hz_count / elapsed
                last_hz_count = 0
                last_hz_time  = now

        for ch, line in enumerate(lines):
            line.set_ydata(buffer[ch])

        for ch in range(n_channels):
            rms     = float(np.sqrt(np.mean(buffer[ch] ** 2)))
            quality = np.clip(rms / (amplitude_uv * 0.5), 0.0, 1.0)
            if rms < 1.0:
                color = STATUS_STOP
            elif quality > 0.8:
                color = MARKER_COLOR
            elif quality > 0.15:
                color = STATUS_OK
            else:
                color = STATUS_PAUSE
            qlines[ch].set_facecolor(color)

        while True:
            try:
                label = marker_q.get_nowait()
                x_pos = window_sec - 0.05
                for ax in axes:
                    ax.axvline(x_pos, color=MARKER_COLOR,
                               linewidth=1.2, linestyle="--",
                               alpha=0.8, zorder=3)
                if axes:
                    axes[0].text(
                        x_pos, amplitude_uv * 0.85,
                        label or "M",
                        color=MARKER_COLOR, fontsize=7,
                        ha="right", va="top",
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
        fig, _update,
        interval=interval_ms,
        blit=False,
        cache_frame_data=False,
    )

    try:
        plt.show()
    except Exception as exc:
        print(f"[Visualizer] Error: {exc}")
    finally:
        print("[Visualizer] Window closed")


class EEGVisualizer:
    """Separate OS process for live EEG plot (dual-monitor dev view)."""

    def __init__(
        self,
        board_shim,
        board_id:      int,
        n_channels:    int   = 8,
        window_sec:    float = WINDOW_SEC,
        plot_hz:       int   = PLOT_HZ,
        amplitude_uv:  float = AMPLITUDE_UV,
        channel_labels       = None,
        fs:            int   = None,
        monitor_index: int   = 1,
    ):
        from brainflow.board_shim import BoardShim

        if fs is None:
            try:
                fs = BoardShim.get_sampling_rate(board_id)
            except Exception:
                fs = 250

        try:
            eeg_ch     = BoardShim.get_eeg_channels(board_id)
            ch_indices = list(eeg_ch[:n_channels])
        except Exception:
            ch_indices = list(range(1, n_channels + 1))

        labels = (channel_labels or CHANNEL_LABELS)[:n_channels]

        self._data_queue   = multiprocessing.Queue(maxsize=300)
        self._marker_queue = multiprocessing.Queue(maxsize=100)
        self._stop_event   = multiprocessing.Event()
        self._pause_event  = multiprocessing.Event()
        self._pause_event.set()

        self._proc_args = (
            self._data_queue,
            self._marker_queue,
            self._stop_event,
            self._pause_event,
            n_channels,
            ch_indices,
            float(window_sec),
            float(fs),
            int(plot_hz),
            float(amplitude_uv),
            labels,
            int(monitor_index),
        )

        self._process = None

    @property
    def data_queue(self) -> multiprocessing.Queue:
        return self._data_queue

    def start(self):
        self._stop_event.clear()
        self._pause_event.set()
        self._process = multiprocessing.Process(
            target=_run_visualizer_process,
            args=self._proc_args,
            daemon=False,
            name="EEGVisualizerProc",
        )
        self._process.start()
        print("[Visualizer] Started")

    def stop(self):
        self._stop_event.set()
        if self._process and self._process.is_alive():
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
        print("[Visualizer] Stopped")

    def pause(self):
        self._pause_event.clear()
        print("[Visualizer] Paused")

    def resume(self):
        self._pause_event.set()
        print("[Visualizer] Resumed")

    def mark(self, label: str = ""):
        try:
            self._marker_queue.put_nowait(label)
        except Exception:
            pass