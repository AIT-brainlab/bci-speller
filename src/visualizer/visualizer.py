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