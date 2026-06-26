"""Concrete MNE FIF recorder implementing RecorderInterface."""

from __future__ import annotations

import contextlib
import io
import queue
import threading
import time
from typing import Any, List, Optional
import numpy as np
from numpy.typing import NDArray

from bci.board.stream import DataStream
from bci.recorder.base import RecorderInterface

# TODO: #16 Remove the visualizer dependency. recording module should only depend on `bci.board`
try:
    from visualizer.utils.common import getdata_offline, save_raw
except ImportError:
    try:
        from utils.common import getdata_offline, save_raw
    except ImportError:
        # Fallback placeholders in case environment is missing these functions
        def getdata_offline(data: Any, board: Any, *args: Any, **kwargs: Any) -> Any:
            return data
        def save_raw(raw: Any, name: str, dir_path: str, participant_id: str) -> str:
            return dir_path


class FifRecorder(RecorderInterface):
    """
    Consumes streamed EEG chunks from a DataStream and saves them as MNE .fif files.

    Replicates the timing stats, windowed saving, validation, and block-level saving
    behaviors of the original experiment's EEGStreamController.
    """

    def __init__(
        self,
        board_id: int,
        recording_dir: str,
        participant_id: str,
        fs: float = 250.0,
        verbose: bool = False,
    ) -> None:
        self.board_id = board_id
        self.recording_dir = recording_dir
        self.participant_id = participant_id
        self.fs = fs
        self.verbose = verbose

        self.stream = DataStream()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = recording, clear = paused/discarding
        self._thread: Optional[threading.Thread] = None

        self._window_index = 0
        self._window_durations: List[float] = []
        self._last_chunk_time: Optional[float] = None
        self._all_chunks: List[NDArray[np.float64]] = []

    def start(self) -> None:
        """Start the background consumer thread."""
        self._stop_event.clear()
        self._pause_event.set()
        self._all_chunks = []
        self._window_durations = []
        self._last_chunk_time = None
        self._thread = threading.Thread(
            target=self._loop,
            name="FifRecorderThread",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background consumer thread."""
        self._stop_event.set()
        self._pause_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def pause(self) -> None:
        """Pause saving incoming chunks to files (data will be discarded)."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume saving incoming chunks to files."""
        self._pause_event.set()
        self._last_chunk_time = None

    def write(self, chunk: Any) -> None:
        """Process, validate, and save one incoming window chunk."""
        # Record poll/arrival duration
        now = time.perf_counter()
        if self._last_chunk_time is not None:
            self._window_durations.append(now - self._last_chunk_time)
        self._last_chunk_time = now

        # Only save and accumulate if not paused
        if not self._pause_event.is_set():
            return

        self._all_chunks.append(chunk)

        idx = self._window_index
        block_name = f"{self.participant_id}_w{idx:04d}_raw"
        
        expected_samples = int(round(self.fs * 0.5))  # window size estimate
        show = self.verbose or (idx < 2) or (idx % 10 == 0)

        if show:
            ok = "OK" if abs(chunk.shape[1] - expected_samples) <= expected_samples * 0.3 else "!"
            print(
                f"  [Recorder] #{idx:04d} | {chunk.shape[0]}x{chunk.shape[1]} | "
                f"{chunk.shape[1]:3d}/{expected_samples} smp | {ok}"
            )

        try:
            data_copy = chunk.copy()
            if not self.verbose:
                # Suppress MNE/matplotlib printing spam
                try:
                    import mne
                    mne.set_log_level("ERROR")
                except Exception:
                    pass
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    raw = getdata_offline(data_copy, self.board_id, n_samples=250, dropEnable=False)
                    save_raw(raw, block_name, self.recording_dir, self.participant_id)
            else:
                raw = getdata_offline(data_copy, self.board_id, n_samples=250, dropEnable=False)
                save_raw(raw, block_name, self.recording_dir, self.participant_id)
        except Exception as exc:
            print(f"[Recorder] W{idx:04d} save failed: {exc}")

        self._window_index += 1

    def save_full_block(self, block_name: str) -> None:
        """Concatenate all accumulated chunks and save as a single MNE fif file."""
        if not self._all_chunks:
            print("[Recorder] No chunks accumulated. Full block file not saved.")
            return

        try:
            full_data = np.concatenate(self._all_chunks, axis=1)
            if self.verbose:
                print(f"[Recorder] Saving full block data shape: {full_data.shape}")
            
            raw = getdata_offline(full_data, self.board_id, n_samples=250, dropEnable=False)
            save_raw(raw, block_name, self.recording_dir, self.participant_id)
            print(f"[Recorder] Full block '{block_name}' saved successfully.")
        except Exception as exc:
            print(f"[Recorder] Full block save failed: {exc}")

    def print_stats(self) -> None:
        """Print timing stats (jitter, interval averages) of chunk arrival times."""
        if not self._window_durations:
            print("[Recorder] No timing stats to show.")
            return
        arr = np.array(self._window_durations) * 1000  # convert to milliseconds
        print("\n=== EEG Stream Timing Report ===")
        print(f"  Total Windows: {len(arr)}")
        print(f"  Mean interval: {arr.mean():.2f} ms")
        print(f"  Std dev:       {arr.std():.2f} ms")
        print(f"  Min/Max:       {arr.min():.2f} ms / {arr.max():.2f} ms")
        print("================================\n")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                chunk = self.stream.get(timeout=0.1)
            except queue.Empty:
                continue

            self.write(chunk)
