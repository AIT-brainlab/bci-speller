from psychopy import visual, core, event
import platform
import os
import sys

# Ensure src/ and visualizer parent are in sys.path
path = os.path.dirname(__file__)
src_path = os.path.join(path, "src")
parent_path = os.path.dirname(path)
for p in (parent_path, src_path, path):
    if p not in sys.path:
        sys.path.insert(0, p)

from visualizer.utils.gui import get_screen_settings, CheckerBoard
import numpy as np
import random
import multiprocessing
import threading
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
import time
import logging
from visualizer.utils.common import getdata_offline, save_raw, drawTextOnScreen
from beeply.notes import *
from visualizer.speller_config import *

import queue
import io
import contextlib
from bci.board.brainflow_board import BrainFlowBoard
from bci.board.synthetic import SyntheticBoard
from bci.recorder.fif import FifRecorder
from bci.ui.signal_monitor import SignalMonitorApp
from visualizer.config import VisualizerConfigError, resolve_plot_params

a = beeps(800)

# Created in initialize_experiment() — never at import time (Windows multiprocessing
# re-imports modules and a module-level Window opens a second board / breaks flicker).
window = None
refresh_rate = 60
epoch_frames = 0
cue_frames = 0
cue = None
cal_start = cal_end = None
targets = {}
flickers = {}
block_break_start = trial_break_start = counter = None
sequence = []
frames = 0
t0 = 0.0

# DEV_DUAL_MONITOR = os.environ.get("DEV_DUAL_MONITOR", "1").strip().lower() in ("1", "true", "yes")
DEV_DUAL_MONITOR = 1
BOARD_SCREEN = int(os.environ.get("BOARD_SCREEN", "0"))
VISUALIZER_MONITOR = int(os.environ.get("VISUALIZER_MONITOR", "1"))
EEG_WINDOW_SEC = float(os.environ.get("EEG_WINDOW_SEC", "0.5"))
EEG_DEBUG = os.environ.get("EEG_DEBUG", "0").strip().lower() in ("1", "true", "yes")
EEG_VERBOSE = os.environ.get("EEG_VERBOSE", "0").strip().lower() in ("1", "true", "yes")
EEG_LOG_EVERY = max(1, int(os.environ.get("EEG_LOG_EVERY", "10")))

_run_handles = {"board": None, "recorder": None, "visualizer": None}
_quitting = False


def log_banner(title):
    line = "=" * 52
    print(f"\n{line}\n  {title}\n{line}")


def log_section(msg):
    print(f"\n--- {msg} ---")


def log_info(tag, msg):
    print(f"  [{tag}] {msg}")


def print_board_layout(board_shim, board_id, window_duration, n_visualizer_channels=8):
    fs = 250
    eeg_rows = list(range(1, 1 + n_visualizer_channels))
    marker_rows, other = [], []

    try:
        fs = BoardShim.get_sampling_rate(board_id)
    except Exception:
        pass
    try:
        eeg_rows = list(BoardShim.get_eeg_channels(board_id))
        marker_rows = list(BoardShim.get_marker_channels(board_id))
        other = list(BoardShim.get_other_channels(board_id))
    except Exception:
        try:
            descr = BoardShim.get_board_descr(board_id)
            if isinstance(descr, dict) and "eeg_channels" in descr:
                eeg_rows = list(descr["eeg_channels"])
        except Exception:
            pass

    try:
        board_shim.get_board_data()
        time.sleep(0.05)
        probe = board_shim.get_board_data()
        n_rows, n_probe = probe.shape if probe is not None and probe.size else (0, 0)
    except Exception:
        # Called before stream starts — static channel/rate info is still valid
        n_rows, n_probe = 0, 0

    expected = int(round(fs * window_duration))
    log_section("Board / EEG timing")
    log_info("Board ID", board_id)
    log_info("Live buffer shape", f"({n_rows} rows, samples vary per pull)")
    log_info("Sampling rate", f"{fs} Hz")
    log_info("Collection window", f"{window_duration} s  ->  expect ~{expected} samples, T~{window_duration*1000:.0f} ms")
    log_info("EEG rows (BrainFlow)", str(eeg_rows))
    log_info("Marker rows", str(marker_rows) if marker_rows else "(see live row count)")
    log_info("Visualizer", f"{n_visualizer_channels} ch -> rows {eeg_rows[:n_visualizer_channels]}")
    log_info("Saved .fif", "17 MNE channels via getdata_offline (normal for Unicorn pipeline)")
    print()
    return fs, eeg_rows


def _process_and_save_window(data_copy, board_id, block_name, recording_dir, participant_id):
    """Hide MNE getdata_offline/save_raw console spam unless EEG_VERBOSE=1."""
    def _do_save():
        raw = getdata_offline(data_copy, board_id, n_samples=250, dropEnable=False)
        save_raw(raw, block_name, recording_dir, participant_id)

    if EEG_VERBOSE or EEG_DEBUG:
        _do_save()
        return
    try:
        import mne
        mne.set_log_level("ERROR")
    except Exception:
        pass
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        _do_save()


def validate_eeg_chunk(data, eeg_indices, fs, window_duration, window_idx):
    """Supervisor check: shape valid and EEG rows exist."""
    if data is None or not hasattr(data, "shape"):
        print(f"[EEG][W{window_idx:04d}] ERROR: data is not an array")
        return False
    if data.ndim != 2:
        print(f"[EEG][W{window_idx:04d}] ERROR: expected 2D, got shape {data.shape}")
        return False
    n_rows, n_samp = data.shape
    if n_samp == 0:
        return False
    bad = [i for i in eeg_indices if i < 0 or i >= n_rows]
    if bad:
        print(f"[EEG][W{window_idx:04d}] ERROR: EEG indices out of range: {bad} (rows={n_rows})")
        return False
    expected = int(round(fs * window_duration))
    lo, hi = int(expected * 0.7), int(expected * 1.35)
    if EEG_DEBUG and window_idx < 3:
        log_info(
            "EEG check",
            f"W{window_idx:04d} shape=({n_rows},{n_samp}) expect ~{expected} in [{lo},{hi}]",
        )
    elif n_samp < lo or n_samp > hi:
        log_info(
            "EEG WARN",
            f"W{window_idx:04d} samples={n_samp} outside [{lo},{hi}] for {window_duration}s@{fs}Hz",
        )
    return True


def measure_refresh_rate(win, n_frames=120):
    """Measure real monitor Hz; a wrong fps slows SSVEP flicker and breaks decoding."""
    win.setMouseVisible(False)
    win.flip()
    clock = core.Clock()
    for _ in range(n_frames):
        win.flip()
    elapsed = clock.getTime()
    reported_raw = win.getActualFrameRate(nIdentical=30, nMaxFrames=120)
    reported = int(round(reported_raw)) if reported_raw not in (None, 0) else None
    if elapsed > 0:
        measured = round(n_frames / elapsed)
        if measured > 0:
            if reported is not None and abs(measured - reported) > 15:
                print(f"[Display] getActualFrameRate={reported} vs measured={measured}, using measured")
            else:
                print(f"[Display] Refresh rate: {measured} Hz (measured)")
            return measured
    if reported is not None:
        print(f"[Display] Refresh rate: {reported} Hz (reported)")
        return reported
    print("[Display] Refresh rate fallback: 60 Hz")
    return 60


def initialize_experiment():
    global window, refresh_rate, epoch_frames, cue_frames
    global cue, cal_start, cal_end, targets, flickers
    global block_break_start, trial_break_start, counter

    system = platform.system()
    width, height = get_screen_settings(system)
    use_fullscr = not DEV_DUAL_MONITOR
    window = visual.Window(
        [width, height],
        screen=BOARD_SCREEN,
        color=[1, 1, 1],
        blendMode="avg",
        useFBO=True,
        units="pix",
        fullscr=use_fullscr,
        allowGUI=DEV_DUAL_MONITOR,
    )
    refresh_rate = measure_refresh_rate(window)
    epoch_frames = int(EPOCH_DURATION * refresh_rate)
    cue_frames = int(CUE_DURATION * refresh_rate)
    print("Epoch frames ==>", epoch_frames)

    cue = visual.Rect(window, width=WIDTH, height=HEIGHT, pos=[0, 0], lineWidth=3, lineColor="red")

    calib_text_start = (
        "Starting callibration phase.Please avoid moving or blinking.\n"
        "You may blink when shifting your gaze.Focus your target on the characters presented with red cue."
    )
    calib_text_end = "Calibration phase completed"
    cal_start = visual.TextStim(window, text=calib_text_start, color=(-1.0, -1.0, -1.0))
    cal_end = visual.TextStim(window, text=calib_text_end, color=(-1.0, -1.0, -1.0))

    targets = {
        f"{target}": visual.TextStim(win=window, text=target, pos=pos, color=(-1.0, -1.0, -1.0), height=35)
        for pos, target in zip(POSITIONS, TARGET_CHARACTERS)
    }

    wave_type = "sin"
    flickers = {
        f"{target}": CheckerBoard(
            window=window,
            size=SIZE,
            frequency=f,
            phase=phase,
            amplitude=AMPLITUDE,
            wave_type=wave_type,
            duration=EPOCH_DURATION,
            fps=refresh_rate,
            base_pos=pos,
            height=HEIGHT,
            width=WIDTH,
        )
        for f, pos, phase, target in zip(FREQS, POSITIONS, PHASES, TARGET_CHARACTERS)
    }

    block_break_text = "Block Break 1 Minute. Please do not move towards the end of break."
    trial_break_text = "Trial Break 15 seconds. Please do not move towards the end of break."
    block_break_start = visual.TextStim(window, text=block_break_text, color=(-1.0, -1.0, -1.0))
    trial_break_start = visual.TextStim(window, text=trial_break_text, color=(-1.0, -1.0, -1.0))
    counter = visual.TextStim(window, text="", pos=(0, 50), color=(-1.0, -1.0, -1.0))

def shutdown_experiment():
    """Stop EEG recorder first, then visualizer and board."""
    global _quitting
    _quitting = True
    rec = _run_handles.get("recorder")
    vis = _run_handles.get("visualizer")
    board = _run_handles.get("board")
    if rec is not None:
        try:
            rec.stop()
        except Exception:
            pass
    if vis is not None:
        try:
            vis.stop()
        except Exception:
            pass
    if board is not None:
        try:
            board.close()
        except Exception:
            pass
    if window is not None:
        try:
            window.close()
        except Exception:
            pass
    core.quit()


def check_escape():
    """Return True if user requested quit (Esc or Q). Works when board window has focus."""
    global _quitting
    if _quitting:
        return True
    keys = event.getKeys(keyList=["escape", "q", "Q"])
    if keys:
        log_section(f"Quit ({keys[0]})")
        shutdown_experiment()
        return True
    return False


def wait_seconds(seconds):
    """Wait but still check Esc/Q (core.wait blocks keyboard)."""
    timer = core.CountdownTimer(seconds)
    while timer.getTime() > 0:
        if check_escape():
            return True
        core.wait(0.05)
    return False


def get_keypress():
    return check_escape()


def eegMarking(board, marker):
    log_info("MARKER", f"Inserted {marker}")
    board.insert_marker(marker)
    time.sleep(0.1)

def flicker(board):
    if EEG_DEBUG:
        log_info("Speller", f"POSITIONS = {POSITIONS}")
    global frames
    global t0
    # For the flickering
    for target in sequence:
        get_keypress()
        target_flicker = flickers[str(target)]
        target_pos = (target_flicker.base_x, target_flicker.base_y)
        marker = MARKERS[str(target)]


        t0 = trialClock.getTime()  # Retrieve time at start of cue presentation

        
        #Display the cue
        cue.pos = target_pos
        for frame in range(cue_frames):
            if check_escape():
                return
            cue.draw()
            window.flip()

        frames = 0
        #flicker random sequence of each speller parallely
        # runInParallel(flicker_subspeller(randomized_subspeller[1]), flicker_subspeller(randomized_subspeller[2]), flicker_subspeller(randomized_subspeller[3]),flicker_subspeller(randomized_subspeller[4]))
        eegMarking(board,marker)
        for frame, j in enumerate(range(epoch_frames)):
            get_keypress()
            for flicker in flickers.values():
                flicker.draw2(frame = frame)
            # target_flicker.draw2(frame = frame)
            frames += 1
            window.flip()
        if wait_seconds(0.5):
            return

def main():
    global sequence
    global trialClock

    initialize_experiment()
    if DEV_DUAL_MONITOR:
        print(
            f"[Dev] Dual monitor: board screen={BOARD_SCREEN}, "
            f"visualizer monitor={VISUALIZER_MONITOR} (Alt+Tab works; not exclusive fullscreen)"
        )

    if EEG_DEBUG and hasattr(BoardShim, "enable_dev_board_logger"):
        BoardShim.enable_dev_board_logger()
    elif hasattr(BoardShim, "disable_dev_board_logger"):
        BoardShim.disable_dev_board_logger()

    # Board initialization using BCI package
    if BOARD_ID <= 0:
        board = SyntheticBoard(
            n_channels=8,
            sampling_rate=250,
            poll_interval_sec=EEG_WINDOW_SEC,
        )
    else:
        board = BrainFlowBoard(
            board_id=BOARD_ID,
            serial_number="UN-2023.08.11",
            poll_interval_sec=EEG_WINDOW_SEC,
        )

    try:
        board.open()
    except Exception as e:
        print(f"Error preparing board: {e}")
        print("The end")
        time.sleep(1)
        sys.exit()

    log_banner("BCI Speller + EEG stream")
    fs, eeg_rows = print_board_layout(board._board_shim, BOARD_ID, EEG_WINDOW_SEC, 8)
    log_section("Controls")
    log_info("Quit", "Focus board window -> Esc or Q | or Ctrl+C in terminal")
    log_info("EEG window", f"{EEG_WINDOW_SEC}s (set EEG_WINDOW_SEC=1.0 for supervisor demo)")
    log_info("Verbose EEG", f"EEG_VERBOSE=1 all windows | default log every {EEG_LOG_EVERY}")
    logging.info("Beginning the experiment")

    # Initialize FifRecorder and add to board subscribers
    recorder = FifRecorder(
        board_id=BOARD_ID,
        recording_dir=RECORDING_DIR,
        participant_id=PARTICIPANT_ID,
        fs=fs,
        verbose=EEG_VERBOSE or EEG_DEBUG,
    )
    board.add_subscriber(recorder.stream)

    _run_handles["board"] = board
    _run_handles["recorder"] = recorder

    try:
        vis_window_sec, vis_plot_hz, vis_amplitude_uv = resolve_plot_params()
    except VisualizerConfigError:
        vis_window_sec, vis_plot_hz, vis_amplitude_uv = resolve_plot_params(
            window_sec=5.0,
            plot_hz=20,
            amplitude_uv=100.0,
        )

    # Initialize refactored signal monitor UI
    visualizer = SignalMonitorApp(
        board=board,
        n_channels=8,
        window_sec=vis_window_sec,
        plot_hz=vis_plot_hz,
        amplitude_uv=vis_amplitude_uv,
        monitor_index=VISUALIZER_MONITOR if DEV_DUAL_MONITOR else 0,
    )
    _run_handles["visualizer"] = visualizer

    while True:
        # Starting the display
        trialClock = core.Clock()
        cal_start.draw()
        window.flip()
        if wait_seconds(3):
            break

        drawTextOnScreen(f"Hi {PARTICIPANT_NAME}.\nStarting the experiment. Please do not move now\nBoard ID: {BOARD_ID}", window)
        if wait_seconds(10):
            break

        board.start_stream()
        recorder.start()
        visualizer.start()
        if DEV_DUAL_MONITOR:
            if wait_seconds(1.5):
                break
        sequence = random.sample(TARGET_CHARACTERS, len(TARGET_CHARACTERS))

        for block in range(NUM_BLOCK):
            for trials in range(NUM_TRIAL):
                get_keypress()

                # Display target characters
                for target in targets.values():
                    target.autoDraw = True
                flicker(board)

                # At the end of the trial, calculate real duration and amount of frames
                t1 = trialClock.getTime()  # Time at end of trial
                elapsed = t1 - t0
                print(f"Time elapsed: {elapsed}")
                print(f"Total frames: {frames}")

                for target in targets.values():
                    target.autoDraw = False

                recorder.pause()
                visualizer.pause()
                countdown_timer = core.CountdownTimer(TRIAL_BREAK)
                if (trials + 1) < NUM_TRIAL:
                    trial_break_start.autoDraw = True
                    while countdown_timer.getTime() > 0:
                        if check_escape():
                            break
                        time_remaining = countdown_timer.getTime()
                        counter.text = f'Block {int(block+1)}/{int(NUM_BLOCK)}. End of trial {int(trials+1)}.\n {int(NUM_TRIAL- (trials+1))} trial(s) left for this block.\nTime remaining: {int(time_remaining)}'
                        counter.draw()
                        window.flip()

                trial_break_start.autoDraw = False
                recorder.resume()
                visualizer.resume()
                window.flip()

            for target in targets.values():
                target.autoDraw = False
            recorder.pause()
            visualizer.pause()
            countdown_timer = core.CountdownTimer(BLOCK_BREAK)
            if (block + 1) < NUM_BLOCK:
                block_break_start.autoDraw = True
                while countdown_timer.getTime() > 0:
                    if check_escape():
                        break
                    time_remaining = countdown_timer.getTime()
                    counter.text = f'End of block {int(block+1)}.\n {int(NUM_BLOCK - (block+1))} block(s) left.\n Time remaining: {int(time_remaining)}'
                    counter.draw()
                    window.flip()

            block_break_start.autoDraw = False
            recorder.resume()
            visualizer.resume()
            window.flip()

        # Adding buffer of 10 sec at the end
        if wait_seconds(10):
            break
        recorder.stop()
        recorder.print_stats()
        visualizer.stop()

        # saving the data from 1 block
        block_name = f'{PARTICIPANT_ID}_raw'
        recorder.save_full_block(block_name)
        drawTextOnScreen('End of experiment, Thank you', window)
        wait_seconds(3)
        break

    if board.get_status().is_open:
        logging.info('Releasing session')
        board.close()

    # cleanup
    window.close()
    core.quit()




if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()