"""
Standalone board test — no GUI.

Reads chunks from ``board.raw_stream`` after starting the streaming loop.

Usage::

    python scripts/test_board_standalone.py
    python scripts/test_board_standalone.py --board-id 8 --serial UN-2023.08.11
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from _bootstrap import bootstrap

bootstrap()

from bci.board.brainflow_board import BrainFlowBoard
from bci.board.synthetic import SyntheticBoard


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test bci.board without GUI.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force BrainFlow synthetic board (board id -1)",
    )
    parser.add_argument("--board-id", type=int, default=None)
    parser.add_argument("--serial", type=str, default=None)
    parser.add_argument("--n-channels", type=int, default=8)
    parser.add_argument("--poll-sec", type=float, default=0.05)
    parser.add_argument("--chunks", type=int, default=10)
    parser.add_argument("--duration-sec", type=float, default=3.0)
    return parser


def _resolve_board_id(explicit: Optional[int], synthetic: bool) -> int:
    if synthetic:
        return -1
    if explicit is not None:
        return explicit
    try:
        from visualizer.speller_config import BOARD_ID

        return int(BOARD_ID)
    except Exception:
        try:
            from speller_config import BOARD_ID

            return int(BOARD_ID)
        except Exception:
            return -1


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
    args = build_arg_parser().parse_args(argv)
    board_id = _resolve_board_id(args.board_id, args.synthetic)
    serial = "" if board_id <= 0 else (args.serial or "UN-2023.08.11")

    print("[test_board] Opening board...", flush=True)
    if board_id <= 0:
        print(
            "[test_board] Synthetic board (console only — for live plot run: "
            "python scripts/run_signal_monitor.py --synthetic)",
            flush=True,
        )
    else:
        print(
            f"[test_board] Hardware board_id={board_id} serial={serial}",
            flush=True,
        )

    board = _create_board(board_id, serial, args.n_channels, args.poll_sec)
    try:
        board.open()
    except Exception as exc:
        print(f"[test_board] Board open failed: {exc}", file=sys.stderr)
        return 1

    status = board.get_status()
    print(f"[test_board] Status: {status}", flush=True)

    board.start_stream()
    print("[test_board] Streaming — reading chunks from raw_stream...", flush=True)

    chunks_read = 0
    total_samples = 0
    deadline = time.monotonic() + args.duration_sec
    while time.monotonic() < deadline and chunks_read < args.chunks:
        try:
            chunk = board.raw_stream.get(timeout=0.5)
            chunks_read += 1
            total_samples += chunk.shape[1]
            print(
                f"  chunk {chunks_read}: shape={chunk.shape} "
                f"dtype={chunk.dtype} samples={chunk.shape[1]}",
                flush=True,
            )
        except Exception:
            continue

    board.stop_stream()
    board.close()
    print(
        f"[test_board] Done — read {chunks_read} chunks, "
        f"{total_samples} total samples.",
        flush=True,
    )
    return 0 if chunks_read > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
