"""
Run the EEG visualizer without the PsychoPy experiment (environment.py).

Example::

    cd visualizer
    copy .env.example .env
    cd ..
    python -m visualizer
"""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import time
from typing import Optional

from visualizer.config.exceptions import VisualizerConfigError
from visualizer.config.settings import get_visualizer_settings
from visualizer.live_monitor_class import EEGVisualizer
from visualizer.stream_feeder import BoardStreamFeeder


def _default_board_id() -> int:
    raw = os.environ.get("BOARD_ID")
    if raw is not None and raw.strip():
        return int(raw)
    try:
        from visualizer.speller_config import BOARD_ID

        return int(BOARD_ID)
    except Exception:
        return 8


def _default_serial() -> str:
    return os.environ.get("BRAINFLOW_SERIAL", "UN-2023.08.11")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone EEG visualizer (BrainFlow + matplotlib).",
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
    parser.add_argument(
        "--n-channels",
        type=int,
        default=8,
        help="Number of EEG channels to plot",
    )
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
        help="Board polling interval for the feeder thread",
    )
    return parser


def run_standalone(argv: Optional[list[str]] = None) -> int:
    """Connect to the board, start the visualizer process, block until exit."""
    from brainflow.board_shim import BoardShim, BrainFlowInputParams

    multiprocessing.freeze_support()

    try:
        settings = get_visualizer_settings()
    except VisualizerConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    args = build_arg_parser().parse_args(argv)
    board_id = args.board_id if args.board_id is not None else _default_board_id()
    serial = args.serial if args.serial is not None else _default_serial()

    params = BrainFlowInputParams()
    params.serial_number = serial
    board_shim = BoardShim(board_id, params)

    print(f"[Standalone] board_id={board_id} serial={serial}")
    print(
        f"[Standalone] plot window={settings.window_sec}s "
        f"refresh={settings.plot_hz}Hz range=±{settings.amplitude_uv}µV"
    )

    try:
        board_shim.prepare_session()
    except Exception as exc:
        print(f"[Standalone] BrainFlow prepare_session failed: {exc}", file=sys.stderr)
        return 1

    board_shim.start_stream()
    board_shim.get_board_data()

    visualizer = EEGVisualizer(
        board_shim=board_shim,
        board_id=board_id,
        n_channels=args.n_channels,
        window_sec=settings.window_sec,
        plot_hz=settings.plot_hz,
        amplitude_uv=settings.amplitude_uv,
        monitor_index=args.monitor,
    )
    feeder = BoardStreamFeeder(
        board_shim=board_shim,
        data_queue=visualizer.data_queue,
        poll_interval_sec=args.poll_sec,
    )

    visualizer.start()
    feeder.start()
    print("[Standalone] EEG visualizer running — close the plot window or press Ctrl+C")

    try:
        while visualizer.is_running:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[Standalone] Interrupted")
    finally:
        feeder.stop()
        visualizer.stop()
        try:
            if board_shim.is_prepared():
                board_shim.stop_stream()
                board_shim.release_session()
        except Exception:
            pass

    return 0
