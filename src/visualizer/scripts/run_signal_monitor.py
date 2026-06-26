"""
Launch the EEG signal monitor (bci.board + ui.signal_monitor).

The UI subscribes to ``board.raw_stream`` via ``StreamBridge`` — same live EEG
plot as ``experiment.py`` / ``standalone.py``, without PsychoPy.

Usage::

    python scripts/run_signal_monitor.py              # speller_config / env board id
    python scripts/run_signal_monitor.py --synthetic  # BrainFlow synthetic board
    python scripts/run_signal_monitor.py --board-id 8 --serial UN-2023.08.11
"""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import time
from typing import Optional

from _bootstrap import bootstrap

_ROOT = bootstrap()

from bci.board.brainflow_board import BrainFlowBoard
from bci.board.synthetic import SyntheticBoard
from bci.ui.signal_monitor import SignalMonitorApp

DEFAULT_HARDWARE_BOARD_ID = 8


def _resolve_board_id(explicit: Optional[int], synthetic: bool) -> int:
    if synthetic:
        return -1
    if explicit is not None:
        return explicit
    raw = os.environ.get("BOARD_ID")
    if raw is not None and raw.strip():
        return int(raw)
    try:
        from visualizer.speller_config import BOARD_ID

        return int(BOARD_ID)
    except Exception:
        try:
            from speller_config import BOARD_ID

            return int(BOARD_ID)
        except Exception:
            return DEFAULT_HARDWARE_BOARD_ID


def _default_serial() -> str:
    return os.environ.get("BRAINFLOW_SERIAL", "UN-2023.08.11")


def _resolve_plot_params(
    window_sec: Optional[float],
    plot_hz: Optional[int],
    amplitude_uv: Optional[float],
) -> tuple[float, int, float]:
    if window_sec is not None and plot_hz is not None and amplitude_uv is not None:
        return float(window_sec), int(plot_hz), float(amplitude_uv)
    try:
        from visualizer.config.settings import get_visualizer_settings

        settings = get_visualizer_settings()
        return (
            float(window_sec if window_sec is not None else settings.window_sec),
            int(plot_hz if plot_hz is not None else settings.plot_hz),
            float(amplitude_uv if amplitude_uv is not None else settings.amplitude_uv),
        )
    except Exception:
        return (
            float(window_sec if window_sec is not None else 5.0),
            int(plot_hz if plot_hz is not None else 20),
            float(amplitude_uv if amplitude_uv is not None else 100.0),
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone EEG signal monitor (bci.board + matplotlib).",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use BrainFlow synthetic board (board id -1, no hardware)",
    )
    parser.add_argument(
        "--board-id",
        type=int,
        default=None,
        help="BrainFlow board id (default: BOARD_ID env or speller_config.BOARD_ID)",
    )
    parser.add_argument(
        "--serial",
        type=str,
        default=None,
        help="Device serial number (default: BRAINFLOW_SERIAL env)",
    )
    parser.add_argument("--n-channels", type=int, default=8)
    parser.add_argument("--window-sec", type=float, default=None)
    parser.add_argument("--plot-hz", type=int, default=None)
    parser.add_argument("--amplitude-uv", type=float, default=None)
    parser.add_argument(
        "--monitor",
        type=int,
        default=int(os.environ.get("VISUALIZER_MONITOR", "1")),
        help="Monitor index for the plot window (0 = primary)",
    )
    parser.add_argument(
        "--poll-sec",
        type=float,
        default=0.05,
        help="Board polling interval for the streaming loop",
    )
    return parser


def _create_board(
    board_id: int,
    serial: str,
    n_channels: int,
    poll_sec: float,
) -> BrainFlowBoard | SyntheticBoard:
    if board_id <= 0:
        return SyntheticBoard(
            n_channels=n_channels,
            sampling_rate=250,
            poll_interval_sec=poll_sec,
        )
    return BrainFlowBoard(
        board_id=board_id,
        serial_number=serial,
        poll_interval_sec=poll_sec,
    )


def main(argv: Optional[list[str]] = None) -> int:
    multiprocessing.freeze_support()

    args = build_arg_parser().parse_args(argv)
    board_id = _resolve_board_id(args.board_id, args.synthetic)
    serial = "" if board_id <= 0 else (args.serial or _default_serial())
    window_sec, plot_hz, amplitude_uv = _resolve_plot_params(
        args.window_sec,
        args.plot_hz,
        args.amplitude_uv,
    )

    if board_id <= 0:
        print("[run_signal_monitor] Using synthetic board (no hardware)")
    print(f"[run_signal_monitor] board_id={board_id} serial={serial or '(none)'}")
    print(
        f"[run_signal_monitor] plot window={window_sec}s "
        f"refresh={plot_hz}Hz range=±{amplitude_uv}µV",
        flush=True,
    )

    board = _create_board(board_id, serial, args.n_channels, args.poll_sec)
    try:
        board.open()
    except Exception as exc:
        print(f"[run_signal_monitor] Board open failed: {exc}", file=sys.stderr)
        return 1

    print(f"[run_signal_monitor] Status: {board.get_status()}", flush=True)
    board.start_stream()

    app = SignalMonitorApp(
        board=board,
        n_channels=args.n_channels,
        window_sec=window_sec,
        plot_hz=plot_hz,
        amplitude_uv=amplitude_uv,
        monitor_index=args.monitor,
    )
    app.start()
    print(
        "[run_signal_monitor] EEG visualizer running — close the plot window or Ctrl+C",
        flush=True,
    )

    try:
        while app.is_running:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[run_signal_monitor] Interrupted", flush=True)
    finally:
        app.stop()
        board.stop_stream()
        board.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
