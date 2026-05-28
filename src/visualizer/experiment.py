# from turtle import fillcolor, pos
# from psychopy import visual, core, event #import some libraries from PsychoPy
# import platform
# import os
# import sys
# path = os.path.dirname(os.path.dirname(__file__)) 
# sys.path.append(path)
# from utils.gui import get_screen_settings, CheckerBoard
# import argparse
# import json
# import numpy as np
# import random
# from multiprocessing import Process
# import multiprocessing
# import threading
# import brainflow
# from brainflow.board_shim import BoardShim, BrainFlowInputParams
# import time
# import logging
# from utils.common import getdata_offline, save_raw, drawTextOnScreen, save_csv
# from beeply.notes import *
# from speller_config import *

# import queue  ###
# from eeg_visualizer import EEGVisualizer ###
# a = beeps(800)
# # Window parameters
# system = platform.system()
# width, height = get_screen_settings(system)

# #create a window
# window = visual.Window([width, height], screen=0, color=[1,1,1],blendMode='avg', useFBO=True, units="pix", fullscr=True)

# # window = visual.Window([1920, 1080], screen=1, color=[1,1,1],blendMode='avg', monitor="hybrid-speller-monitor", useFBO=True, units="deg", fullscr=True)
# # mywin = visual.Window(SCREEN_SIZE, color="black",monitor="Experiment Monitor" , units='norm',screen=SCREEN_NUM,fullscr=True) 
# refresh_rate = round(window.getActualFrameRate())
# print("Refresh Rate ==>", refresh_rate)   



# # Time conversion to frames
# epoch_frames = int(EPOCH_DURATION * refresh_rate)
# print("Epoch frames ==>",epoch_frames)
# cue_frames = int(CUE_DURATION * refresh_rate)   


# #Presentation content

# cue = visual.Rect(window, width=WIDTH, height=HEIGHT, pos=[0, 0], lineWidth=3, lineColor='red')

# calib_text_start = "Starting callibration phase.Please avoid moving or blinking.\n\
# You may blink when shifting your gaze.Focus your target on the characters presented with red cue."

# calib_text_end = "Calibration phase completed"
# cal_start = visual.TextStim(window, text=calib_text_start, color=(-1., -1., -1.))
# cal_end = visual.TextStim(window, text=calib_text_end, color=(-1., -1., -1.))

# targets = {f"{target}": visual.TextStim(win=window, text=target, pos=pos, color=(-1., -1., -1.), height=35)
#         for pos, target in zip(POSITIONS, TARGET_CHARACTERS)}


# wave_type = "sin"

# flickers = {f"{target}": CheckerBoard(window=window, size=SIZE, frequency=f, phase=phase, amplitude=AMPLITUDE, 
#                                     wave_type=wave_type, duration=EPOCH_DURATION, fps=refresh_rate,
#                                     base_pos=pos, height = HEIGHT, width=WIDTH)
#             for f, pos, phase, target in zip(FREQS, POSITIONS, PHASES, TARGET_CHARACTERS)}


# block_break_text = "Block Break 1 Minute. Please do not move towards the end of break."
# trial_break_text = "Trial Break 15 seconds. Please do not move towards the end of break."
# block_break_start = visual.TextStim(window, text=block_break_text, color=(-1., -1., -1.))
# trial_break_start = visual.TextStim(window, text=trial_break_text, color=(-1., -1., -1.))
# counter = visual.TextStim(window, text='', pos=(0, 50), color=(-1., -1., -1.))

# ###
# class EEGStreamController:
#     def __init__(self, board_shim, window_duration, board_id,
#                  recording_dir, participant_id):
#         self.board_shim      = board_shim
#         self.window_duration = window_duration  # seconds per window e.g. 1.0
#         self.board_id        = board_id
#         self.recording_dir   = recording_dir
#         self.participant_id  = participant_id
#         self._stop_event     = threading.Event()
#         self._pause_event    = threading.Event()
#         self._pause_event.set()   # not paused at start
#         self._thread         = None
#         self._lock           = threading.Lock()
#         self._window_index   = 0
#         self._window_durations = []
#         self._data_queue     = queue.Queue()
#         ###
#         ###
#     def start(self):
#         self.board_shim.get_board_data()
#         self._stop_event.clear()
#         self._thread = threading.Thread(
#             target=self._collection_loop,
#             name="EEGStreamController",
#             daemon=True)
#         self._thread.start()
#         print(f"[EEGStream] Started | window_duration = {self.window_duration}s")
#     def stop(self):
#         self._stop_event.set()
#         self._pause_event.set()  # unblock if paused
#         if self._thread and self._thread.is_alive():
#             self._thread.join(timeout=self.window_duration + 2.0)
#         print(f"[EEGStream] Stopped | total windows collected = {self._window_index}")
#     def pause(self):
#         self._pause_event.clear()
#         print("[EEGStream] Paused")
#     def resume(self):
#         _ = self.board_shim.get_board_data()  # flush stale buffer
#         self._pause_event.set()
#         print("[EEGStream] Resumed (stale buffer flushed)")
#     def print_stats(self):
#         with self._lock:
#             durations = list(self._window_durations)
#         if not durations:
#             print("[EEGStream] No timing stats to show.")
#             return
#         arr = np.array(durations) * 1000  # convert to milliseconds
#         print("\n[EEGStream] ===== Window Timing Report =====")
#         print(f"  Total windows  : {len(arr)}")
#         print(f"  Target         : {self.window_duration * 1000:.1f} ms")
#         print(f"  Mean           : {arr.mean():.2f} ms")
#         print(f"  Std dev        : {arr.std():.2f} ms")
#         print(f"  Min            : {arr.min():.2f} ms")
#         print(f"  Max            : {arr.max():.2f} ms")
#         print("==========================================\n")
#     def _collection_loop(self):
#         while not self._stop_event.is_set():
#             self._pause_event.wait()
#             if self._stop_event.is_set():
#                 break
#             window_start = time.perf_counter()
#             coarse_sleep = self.window_duration - 0.002
#             if coarse_sleep > 0:
#                 time.sleep(coarse_sleep)
#             while time.perf_counter() - window_start < self.window_duration:
#                 pass  # busy-wait final 2ms
#             data           = self.board_shim.get_board_data()
#             actual_elapsed = time.perf_counter() - window_start
#             with self._lock:
#                 self._window_durations.append(actual_elapsed)
#             if data.shape[1] == 0:
#                 print(f"[EEGStream] Window {self._window_index:04d} WARNING: 0 samples!")
#                 self._window_index += 1
#                 continue
#             print(
#                 f"[EEG] W:{self._window_index:03d} | "
#                 f"S:{data.shape[1]} | "
#                 f"T:{actual_elapsed*1000:.1f}ms"
#             )
#             try:
#                 data_copy  = data.copy()
#                 raw        = getdata_offline(data_copy, self.board_id,n_samples=250, dropEnable=False)
#                 block_name = f"{self.participant_id}_w{self._window_index:04d}_raw"
#                 save_raw(raw, block_name, self.recording_dir, self.participant_id)
#             except Exception as exc:
#                 print(f"[EEGStream] Save error window {self._window_index}: {exc}")
#             self._data_queue.put(data.copy())
            
#             self._window_index += 1
#  ###
# def get_keypress():
#     keys = event.getKeys()
#     if keys and keys[0] == 'escape':
#         window.close()
#         core.quit()
#     else: 
#         return None


# def eegMarking(board,marker):
#     print(f"[MARKER] Inserted marker {marker}")
#     board.insert_marker(marker)
#     time.sleep(0.1)

# def flicker(board):
#     print(f"[INFO] POSITIONS = {POSITIONS}")
#     global frames
#     global t0
#     # For the flickering
#     for target in sequence:
#         get_keypress()
#         target_flicker = flickers[str(target)]
#         target_pos = (target_flicker.base_x, target_flicker.base_y)
#         marker = MARKERS[str(target)]


#         t0 = trialClock.getTime()  # Retrieve time at start of cue presentation

        
#         #Display the cue
#         cue.pos = target_pos
#         for frame in range(cue_frames):
#                 cue.draw()
#                 window.flip()

#         frames = 0
#         #flicker random sequence of each speller parallely
#         # runInParallel(flicker_subspeller(randomized_subspeller[1]), flicker_subspeller(randomized_subspeller[2]), flicker_subspeller(randomized_subspeller[3]),flicker_subspeller(randomized_subspeller[4]))
#         eegMarking(board,marker)
#         for frame, j in enumerate(range(epoch_frames)):
#             get_keypress()
#             for flicker in flickers.values():
#                 flicker.draw2(frame = frame)
#             # target_flicker.draw2(frame = frame)
#             frames += 1
#             window.flip()
#         core.wait(0.5)

# def main():
#     global sequence
#     global trialClock

#     BoardShim.enable_dev_board_logger()

#     #brainflow initialization 
#     params = BrainFlowInputParams()
#     params.serial_number = "UN-2023.08.11"
#     # params.serial_port = serial_port
#     board_shim = BoardShim(BOARD_ID, params)

#     #prepare board
#     try:
#         board_shim.prepare_session()
#     except brainflow.board_shim.BrainFlowError as e:
#         print(f"Error: {e}")
#         print("The end")
#         time.sleep(1)
#         sys.exit()
#     #board start streaming
#     board_shim.start_stream()

#     logging.info('Begining the experiment')
# ###
#     eeg_controller = EEGStreamController(
#     board_shim      = board_shim,
#     window_duration = 1.0,   
#     board_id        = BOARD_ID,
#     recording_dir   = RECORDING_DIR,
#     participant_id  = PARTICIPANT_ID,)
#     visualizer = EEGVisualizer(
#         board_shim    = board_shim,
#         board_id      = BOARD_ID,
#         n_channels    = 8,          # Unicorn has 8 EEG channels
#         window_sec    = 5,          # show 5 seconds of signal
#         plot_hz       = 20,         # refresh 20 times per second
#         amplitude_uv  = 100,        # ±100 µV display range
#     )
# ###
#     while True:

#         # Starting the display
#         trialClock = core.Clock()
#         cal_start.draw()
#         window.flip()
#         core.wait(3)


#         drawTextOnScreen(f"Hi {PARTICIPANT_NAME}.\nStarting the experiment.Please do not move now\nBoard ID: {BOARD_ID}",window)
#         #Adding buffer of 10 sec at the beginning of experiment
#         core.wait(10)
# ###
#         eeg_controller.start()
#         visualizer.start()
# ###
#         sequence = random.sample(TARGET_CHARACTERS, len(TARGET_CHARACTERS))

#         for block in range(NUM_BLOCK):
#             for trials in range(NUM_TRIAL):
#                 get_keypress()
#                 # Drawing display box

#                 # Drawing the grid
#                 # Display target characters
#                 for target in targets.values():
#                     target.autoDraw = True
#                     # get_keypress()
#                 flicker(board_shim)

#                 # At the end of the trial, calculate real duration and amount of frames
#                 t1 = trialClock.getTime()  # Time at end of trial
#                 elapsed = t1 - t0
#                 print(f"Time elapsed: {elapsed}")
#                 print(f"Total frames: {frames}")

#                 for target in targets.values():
#                     target.autoDraw = False
#                     ###
#                 eeg_controller.pause()
#                 ###
#                 countdown_timer = core.CountdownTimer(TRIAL_BREAK)
#                 if (trials + 1) < NUM_TRIAL: 
#                     # drawTextOnScreen('trials Break 30 sec. You can blink but please donot move.',window)
#                     # core.wait(BLOCK_BREAK)
#                     trial_break_start.autoDraw = True
#                     while countdown_timer.getTime() > 0:
#                         time_remaining = countdown_timer.getTime()
#                         counter.text = f'Block {int(block+1)}/{int(NUM_BLOCK)}. End of trial {int(trials+1)}.\n {int(NUM_TRIAL- (trials+1))} trial(s) left for this block.\nTime remaining: {int(time_remaining)}'
#                         counter.draw()
#                         window.flip()

#                 # trials += 1
#                 trial_break_start.autoDraw = False
#                 ###
#                 eeg_controller.resume()
#                 ###
#                 window.flip()

#             for target in targets.values():
#                 target.autoDraw = False
#             ###
#             eeg_controller.pause()
#             ###
#             countdown_timer = core.CountdownTimer(BLOCK_BREAK)
#             if (block + 1) < NUM_BLOCK: 
#                 # drawTextOnScreen('Block Break 30 sec. You can blink but please donot move.',window)
#                 # core.wait(BLOCK_BREAK)
#                 block_break_start.autoDraw = True
#                 while countdown_timer.getTime() > 0:
#                     time_remaining = countdown_timer.getTime()
#                     counter.text = f'End of block {int(block+1)}.\n {int(NUM_BLOCK- (block+1))} block(s) left.\n Time remaining: {int(time_remaining)}'
#                     counter.draw()
#                     window.flip()

#             # block += 1
#             block_break_start.autoDraw = False
#             ###
#             eeg_controller.resume()
#             ###
#             window.flip()

        
#         #Adding buffer of 10 sec at the end
#         core.wait(10)
#         ###
#         eeg_controller.stop()
#         eeg_controller.print_stats()
#         visualizer.stop()
# ###
#         # saving the data from 1 block
#         block_name = f'{PARTICIPANT_ID}_raw'
#         data = board_shim.get_board_data()
#         data_copy = data.copy()
#         raw = getdata_offline(data_copy,BOARD_ID,n_samples = 250,dropEnable = False)
#         save_raw(raw,block_name,RECORDING_DIR, PARTICIPANT_ID)
#         # save_csv(data, RECORDING_DIR, PARTICIPANT_ID)
#         drawTextOnScreen('End of experiment, Thank you',window)
#         core.wait(3)
#         break


#     if board_shim.is_prepared():
#         logging.info('Releasing session')
#         # stop board to stream
#         board_shim.stop_stream()
#         board_shim.release_session()

#     #cleanup
#     window.close()
#     core.quit()




# if __name__ == "__main__":
#     main()

























# from psychopy import visual, core, event
# import platform
# import os
# import sys
# path = os.path.dirname(os.path.dirname(__file__))
# sys.path.append(path)
# from utils.gui import get_screen_settings, CheckerBoard
# import numpy as np
# import random
# import multiprocessing
# import threading
# import brainflow
# from brainflow.board_shim import BoardShim, BrainFlowInputParams
# import time
# import logging
# from utils.common import getdata_offline, save_raw, drawTextOnScreen
# from beeply.notes import *
# from speller_config import *

# import queue
# from eeg_visualizer import EEGVisualizer

# a = beeps(800)

# # Created in initialize_experiment() — never at import time (Windows multiprocessing
# # re-imports modules and a module-level Window opens a second board / breaks flicker).
# window = None
# refresh_rate = 60
# epoch_frames = 0
# cue_frames = 0
# cue = None
# cal_start = cal_end = None
# targets = {}
# flickers = {}
# block_break_start = trial_break_start = counter = None
# sequence = []
# frames = 0
# t0 = 0.0

# # Developer dual-monitor: board on BOARD_SCREEN, EEG plot on VISUALIZER_MONITOR.
# # Set DEV_DUAL_MONITOR=0 for single-monitor fullscreen production runs.
# DEV_DUAL_MONITOR = os.environ.get("DEV_DUAL_MONITOR", "1").strip().lower() in ("1", "true", "yes")
# BOARD_SCREEN = int(os.environ.get("BOARD_SCREEN", "0"))
# VISUALIZER_MONITOR = int(os.environ.get("VISUALIZER_MONITOR", "1"))


# def measure_refresh_rate(win, n_frames=120):
#     """Measure real monitor Hz; a wrong fps slows SSVEP flicker and breaks decoding."""
#     win.setMouseVisible(False)
#     win.flip()
#     clock = core.Clock()
#     for _ in range(n_frames):
#         win.flip()
#     elapsed = clock.getTime()
#     reported = round(win.getActualFrameRate(nIdentical=30, nMaxFrames=120))
#     if elapsed > 0:
#         measured = round(n_frames / elapsed)
#         if measured > 0:
#             if reported > 0 and abs(measured - reported) > 15:
#                 print(f"[Display] getActualFrameRate={reported} vs measured={measured}, using measured")
#             else:
#                 print(f"[Display] Refresh rate: {measured} Hz (measured)")
#             return measured
#     if reported > 0:
#         print(f"[Display] Refresh rate: {reported} Hz (reported)")
#         return reported
#     print("[Display] Refresh rate fallback: 60 Hz")
#     return 60


# def initialize_experiment():
#     global window, refresh_rate, epoch_frames, cue_frames
#     global cue, cal_start, cal_end, targets, flickers
#     global block_break_start, trial_break_start, counter

#     system = platform.system()
#     width, height = get_screen_settings(system)
#     use_fullscr = not DEV_DUAL_MONITOR
#     window = visual.Window(
#         [width, height],
#         screen=BOARD_SCREEN,
#         color=[1, 1, 1],
#         blendMode="avg",
#         useFBO=True,
#         units="pix",
#         fullscr=use_fullscr,
#         allowGUI=DEV_DUAL_MONITOR,
#     )
#     refresh_rate = measure_refresh_rate(window)
#     epoch_frames = int(EPOCH_DURATION * refresh_rate)
#     cue_frames = int(CUE_DURATION * refresh_rate)
#     print("Epoch frames ==>", epoch_frames)

#     cue = visual.Rect(window, width=WIDTH, height=HEIGHT, pos=[0, 0], lineWidth=3, lineColor="red")

#     calib_text_start = (
#         "Starting callibration phase.Please avoid moving or blinking.\n"
#         "You may blink when shifting your gaze.Focus your target on the characters presented with red cue."
#     )
#     calib_text_end = "Calibration phase completed"
#     cal_start = visual.TextStim(window, text=calib_text_start, color=(-1.0, -1.0, -1.0))
#     cal_end = visual.TextStim(window, text=calib_text_end, color=(-1.0, -1.0, -1.0))

#     targets = {
#         f"{target}": visual.TextStim(win=window, text=target, pos=pos, color=(-1.0, -1.0, -1.0), height=35)
#         for pos, target in zip(POSITIONS, TARGET_CHARACTERS)
#     }

#     wave_type = "sin"
#     flickers = {
#         f"{target}": CheckerBoard(
#             window=window,
#             size=SIZE,
#             frequency=f,
#             phase=phase,
#             amplitude=AMPLITUDE,
#             wave_type=wave_type,
#             duration=EPOCH_DURATION,
#             fps=refresh_rate,
#             base_pos=pos,
#             height=HEIGHT,
#             width=WIDTH,
#         )
#         for f, pos, phase, target in zip(FREQS, POSITIONS, PHASES, TARGET_CHARACTERS)
#     }

#     block_break_text = "Block Break 1 Minute. Please do not move towards the end of break."
#     trial_break_text = "Trial Break 15 seconds. Please do not move towards the end of break."
#     block_break_start = visual.TextStim(window, text=block_break_text, color=(-1.0, -1.0, -1.0))
#     trial_break_start = visual.TextStim(window, text=trial_break_text, color=(-1.0, -1.0, -1.0))
#     counter = visual.TextStim(window, text="", pos=(0, 50), color=(-1.0, -1.0, -1.0))

# ###
# class EEGStreamController:
#     def __init__(self, board_shim, window_duration, board_id,
#                  recording_dir, participant_id):
#         self.board_shim      = board_shim
#         self.window_duration = window_duration  # seconds per window e.g. 1.0
#         self.board_id        = board_id
#         self.recording_dir   = recording_dir
#         self.participant_id  = participant_id
#         self._stop_event     = threading.Event()
#         self._pause_event    = threading.Event()
#         self._pause_event.set()   # not paused at start
#         self._thread         = None
#         self._lock           = threading.Lock()
#         self._window_index   = 0
#         self._window_durations = []
#         self._data_queue     = queue.Queue()
#         ###
#         self._subscribers    = [] 
#     def add_subscriber(self, q):
#         self._subscribers.append(q)
#         ###
#     def start(self):
#         self.board_shim.get_board_data()
#         self._stop_event.clear()
#         self._thread = threading.Thread(
#             target=self._collection_loop,
#             name="EEGStreamController",
#             daemon=True)
#         self._thread.start()
#         print(f"[EEGStream] Started | window_duration = {self.window_duration}s")
#     def stop(self):
#         self._stop_event.set()
#         self._pause_event.set()  # unblock if paused
#         if self._thread and self._thread.is_alive():
#             self._thread.join(timeout=self.window_duration + 2.0)
#         print(f"[EEGStream] Stopped | total windows collected = {self._window_index}")
#     def pause(self):
#         self._pause_event.clear()
#         print("[EEGStream] Paused")
#     def resume(self):
#         _ = self.board_shim.get_board_data()  # flush stale buffer
#         self._pause_event.set()
#         print("[EEGStream] Resumed (stale buffer flushed)")
#     def print_stats(self):
#         with self._lock:
#             durations = list(self._window_durations)
#         if not durations:
#             print("[EEGStream] No timing stats to show.")
#             return
#         arr = np.array(durations) * 1000  # convert to milliseconds
#         print("\n[EEGStream] ===== Window Timing Report =====")
#         print(f"  Total windows  : {len(arr)}")
#         print(f"  Target         : {self.window_duration * 1000:.1f} ms")
#         print(f"  Mean           : {arr.mean():.2f} ms")
#         print(f"  Std dev        : {arr.std():.2f} ms")
#         print(f"  Min            : {arr.min():.2f} ms")
#         print(f"  Max            : {arr.max():.2f} ms")
#         print("==========================================\n")
#     def _collection_loop(self):
#         while not self._stop_event.is_set():
#             self._pause_event.wait()
#             if self._stop_event.is_set():
#                 break
#             window_start = time.perf_counter()
#             while True:
#                 remaining = self.window_duration - (time.perf_counter() - window_start)
#                 if remaining <= 0:
#                     break
#                 time.sleep(min(remaining, 0.005))
#             data           = self.board_shim.get_board_data()
#             actual_elapsed = time.perf_counter() - window_start
#             with self._lock:
#                 self._window_durations.append(actual_elapsed)
#             if data.shape[1] == 0:
#                 print(f"[EEGStream] Window {self._window_index:04d} WARNING: 0 samples!")
#                 self._window_index += 1
#                 continue
#             print(
#                 f"[EEG] W:{self._window_index:03d} | "
#                 f"S:{data.shape[1]} | "
#                 f"T:{actual_elapsed*1000:.1f}ms"
#             )
#             try:
#                 data_copy  = data.copy()
#                 raw        = getdata_offline(data_copy, self.board_id,n_samples=250, dropEnable=False)
#                 block_name = f"{self.participant_id}_w{self._window_index:04d}_raw"
#                 save_raw(raw, block_name, self.recording_dir, self.participant_id)
#             except Exception as exc:
#                 print(f"[EEGStream] Save error window {self._window_index}: {exc}")
#             self._data_queue.put(data.copy())
#             for sub_q in self._subscribers:
#                 try:
#                     sub_q.put_nowait(data.copy())
#                 except Exception:
#                     pass
#             self._window_index += 1
#  ###
# def get_keypress():
#     keys = event.getKeys()
#     if keys and keys[0] == 'escape':
#         window.close()
#         core.quit()
#     else: 
#         return None


# def eegMarking(board,marker):
#     print(f"[MARKER] Inserted marker {marker}")
#     board.insert_marker(marker)
#     time.sleep(0.1)

# def flicker(board):
#     print(f"[INFO] POSITIONS = {POSITIONS}")
#     global frames
#     global t0
#     # For the flickering
#     for target in sequence:
#         get_keypress()
#         target_flicker = flickers[str(target)]
#         target_pos = (target_flicker.base_x, target_flicker.base_y)
#         marker = MARKERS[str(target)]


#         t0 = trialClock.getTime()  # Retrieve time at start of cue presentation

        
#         #Display the cue
#         cue.pos = target_pos
#         for frame in range(cue_frames):
#                 cue.draw()
#                 window.flip()

#         frames = 0
#         #flicker random sequence of each speller parallely
#         # runInParallel(flicker_subspeller(randomized_subspeller[1]), flicker_subspeller(randomized_subspeller[2]), flicker_subspeller(randomized_subspeller[3]),flicker_subspeller(randomized_subspeller[4]))
#         eegMarking(board,marker)
#         for frame, j in enumerate(range(epoch_frames)):
#             get_keypress()
#             for flicker in flickers.values():
#                 flicker.draw2(frame = frame)
#             # target_flicker.draw2(frame = frame)
#             frames += 1
#             window.flip()
#         core.wait(0.5)

# def main():
#     global sequence
#     global trialClock

#     initialize_experiment()
#     if DEV_DUAL_MONITOR:
#         print(
#             f"[Dev] Dual monitor: board screen={BOARD_SCREEN}, "
#             f"visualizer monitor={VISUALIZER_MONITOR} (Alt+Tab works; not exclusive fullscreen)"
#         )

#     BoardShim.enable_dev_board_logger()

#     #brainflow initialization 
#     params = BrainFlowInputParams()
#     params.serial_number = "UN-2023.08.11"
#     # params.serial_port = serial_port
#     board_shim = BoardShim(BOARD_ID, params)

#     #prepare board
#     try:
#         board_shim.prepare_session()
#     except brainflow.board_shim.BrainFlowError as e:
#         print(f"Error: {e}")
#         print("The end")
#         time.sleep(1)
#         sys.exit()
#     #board start streaming
#     board_shim.start_stream()

#     logging.info('Begining the experiment')
# ###
#     eeg_controller = EEGStreamController(
#     board_shim      = board_shim,
#     window_duration = 0.5,   
#     board_id        = BOARD_ID,
#     recording_dir   = RECORDING_DIR,
#     participant_id  = PARTICIPANT_ID,)
#     visualizer = EEGVisualizer(
#         board_shim      = board_shim,
#         board_id        = BOARD_ID,
#         n_channels      = 8,
#         window_sec      = 5,
#         plot_hz         = 20,
#         amplitude_uv    = 100,
#         monitor_index   = VISUALIZER_MONITOR if DEV_DUAL_MONITOR else 0,
#     )
#     eeg_controller.add_subscriber(visualizer.data_queue)
# ###
#     while True:

#         # Starting the display
#         trialClock = core.Clock()
#         cal_start.draw()
#         window.flip()
#         core.wait(3)


#         drawTextOnScreen(f"Hi {PARTICIPANT_NAME}.\nStarting the experiment.Please do not move now\nBoard ID: {BOARD_ID}",window)
#         #Adding buffer of 10 sec at the beginning of experiment
#         core.wait(10)
# ###
#         eeg_controller.start()
#         visualizer.start()
#         if DEV_DUAL_MONITOR:
#             core.wait(1.5)
# ###
#         sequence = random.sample(TARGET_CHARACTERS, len(TARGET_CHARACTERS))

#         for block in range(NUM_BLOCK):
#             for trials in range(NUM_TRIAL):
#                 get_keypress()
#                 # Drawing display box

#                 # Drawing the grid
#                 # Display target characters
#                 for target in targets.values():
#                     target.autoDraw = True
#                     # get_keypress()
#                 flicker(board_shim)

#                 # At the end of the trial, calculate real duration and amount of frames
#                 t1 = trialClock.getTime()  # Time at end of trial
#                 elapsed = t1 - t0
#                 print(f"Time elapsed: {elapsed}")
#                 print(f"Total frames: {frames}")

#                 for target in targets.values():
#                     target.autoDraw = False
#                     ###
#                 eeg_controller.pause()
#                 visualizer.pause()
#                 countdown_timer = core.CountdownTimer(TRIAL_BREAK)
#                 if (trials + 1) < NUM_TRIAL: 
#                     # drawTextOnScreen('trials Break 30 sec. You can blink but please donot move.',window)
#                     # core.wait(BLOCK_BREAK)
#                     trial_break_start.autoDraw = True
#                     while countdown_timer.getTime() > 0:
#                         time_remaining = countdown_timer.getTime()
#                         counter.text = f'Block {int(block+1)}/{int(NUM_BLOCK)}. End of trial {int(trials+1)}.\n {int(NUM_TRIAL- (trials+1))} trial(s) left for this block.\nTime remaining: {int(time_remaining)}'
#                         counter.draw()
#                         window.flip()

#                 # trials += 1
#                 trial_break_start.autoDraw = False
#                 ###
#                 eeg_controller.resume()
#                 visualizer.resume()
#                 window.flip()

#             for target in targets.values():
#                 target.autoDraw = False
#             eeg_controller.pause()
#             visualizer.pause()
#             countdown_timer = core.CountdownTimer(BLOCK_BREAK)
#             if (block + 1) < NUM_BLOCK: 
#                 # drawTextOnScreen('Block Break 30 sec. You can blink but please donot move.',window)
#                 # core.wait(BLOCK_BREAK)
#                 block_break_start.autoDraw = True
#                 while countdown_timer.getTime() > 0:
#                     time_remaining = countdown_timer.getTime()
#                     counter.text = f'End of block {int(block+1)}.\n {int(NUM_BLOCK- (block+1))} block(s) left.\n Time remaining: {int(time_remaining)}'
#                     counter.draw()
#                     window.flip()

#             # block += 1
#             block_break_start.autoDraw = False
#             ###
#             eeg_controller.resume()
#             visualizer.resume()
#             window.flip()

        
#         #Adding buffer of 10 sec at the end
#         core.wait(10)
#         ###
#         eeg_controller.stop()
#         eeg_controller.print_stats()
#         visualizer.stop()
# ###
#         # saving the data from 1 block
#         block_name = f'{PARTICIPANT_ID}_raw'
#         data = board_shim.get_board_data()
#         data_copy = data.copy()
#         raw = getdata_offline(data_copy,BOARD_ID,n_samples = 250,dropEnable = False)
#         save_raw(raw,block_name,RECORDING_DIR, PARTICIPANT_ID)
#         # save_csv(data, RECORDING_DIR, PARTICIPANT_ID)
#         drawTextOnScreen('End of experiment, Thank you',window)
#         core.wait(3)
#         break


#     if board_shim.is_prepared():
#         logging.info('Releasing session')
#         # stop board to stream
#         board_shim.stop_stream()
#         board_shim.release_session()

#     #cleanup
#     window.close()
#     core.quit()




# if __name__ == "__main__":
#     multiprocessing.freeze_support()
#     main()











from psychopy import visual, core, event
import platform
import os
import sys
path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)
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
from visualizer.eeg_visualizer import EEGVisualizer

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
DEV_DUAL_MONITOR = 0
BOARD_SCREEN = int(os.environ.get("BOARD_SCREEN", "0"))
VISUALIZER_MONITOR = int(os.environ.get("VISUALIZER_MONITOR", "1"))
EEG_WINDOW_SEC = float(os.environ.get("EEG_WINDOW_SEC", "0.5"))
EEG_DEBUG = os.environ.get("EEG_DEBUG", "0").strip().lower() in ("1", "true", "yes")
EEG_VERBOSE = os.environ.get("EEG_VERBOSE", "0").strip().lower() in ("1", "true", "yes")
EEG_LOG_EVERY = max(1, int(os.environ.get("EEG_LOG_EVERY", "10")))

_run_handles = {"board_shim": None, "eeg_controller": None, "visualizer": None}
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

    board_shim.get_board_data()
    time.sleep(0.05)
    probe = board_shim.get_board_data()
    n_rows, n_probe = probe.shape if probe is not None and probe.size else (0, 0)

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
    reported = round(win.getActualFrameRate(nIdentical=30, nMaxFrames=120))
    if elapsed > 0:
        measured = round(n_frames / elapsed)
        if measured > 0:
            if reported > 0 and abs(measured - reported) > 15:
                print(f"[Display] getActualFrameRate={reported} vs measured={measured}, using measured")
            else:
                print(f"[Display] Refresh rate: {measured} Hz (measured)")
            return measured
    if reported > 0:
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

###
class EEGStreamController:
    """
    Pull EEG in fixed wall-clock windows (perf_counter), because headset timestamps
    are unreliable. window_duration=1.0 means ~1s between get_board_data() calls.
    """
    def __init__(self, board_shim, window_duration, board_id,
                 recording_dir, participant_id, eeg_row_indices=None):
        self.board_shim      = board_shim
        self.window_duration = float(window_duration)
        self.board_id        = board_id
        self.recording_dir   = recording_dir
        self.participant_id  = participant_id
        try:
            self.fs = BoardShim.get_sampling_rate(board_id)
        except Exception:
            self.fs = 250
        if eeg_row_indices is None:
            try:
                eeg_row_indices = list(BoardShim.get_eeg_channels(board_id))
            except Exception:
                eeg_row_indices = list(range(1, 9))
        self.eeg_row_indices = list(eeg_row_indices)
        self._stop_event     = threading.Event()
        self._pause_event    = threading.Event()
        self._pause_event.set()   # set = running, clear = paused
        self._thread         = None
        self._lock           = threading.Lock()
        self._window_index   = 0
        self._window_durations = []
        self._data_queue     = queue.Queue()
        self._subscribers    = []
        self._save_while_paused = False
    def add_subscriber(self, q):
        self._subscribers.append(q)
        ###
    def start(self):
        self.board_shim.get_board_data()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._collection_loop,
            name="EEGStreamController",
            daemon=True)
        self._thread.start()
        log_info("EEGStream", f"Started | window = {self.window_duration}s | log every {EEG_LOG_EVERY} windows")
    def stop(self):
        self._stop_event.set()
        self._pause_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        log_info("EEGStream", f"Stopped | windows saved = {self._window_index}")
    def pause(self):
        self._pause_event.clear()
        log_info("EEGStream", "Paused (no save/stream until resume)")
    def resume(self):
        _ = self.board_shim.get_board_data()
        self._pause_event.set()
        log_info("EEGStream", "Resumed")
    def print_stats(self):
        with self._lock:
            durations = list(self._window_durations)
        if not durations:
            print("[EEGStream] No timing stats to show.")
            return
        arr = np.array(durations) * 1000  # convert to milliseconds
        log_section("EEG timing report")
        log_info("Windows", str(len(arr)))
        log_info("Target ms", f"{self.window_duration * 1000:.1f}")
        log_info("Mean ms", f"{arr.mean():.2f}")
        log_info("Std ms", f"{arr.std():.2f}")
        log_info("Min/Max ms", f"{arr.min():.2f} / {arr.max():.2f}")
        print()
    def _collection_loop(self):
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break
            window_start = time.perf_counter()
            while True:
                remaining = self.window_duration - (time.perf_counter() - window_start)
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.005))
            data           = self.board_shim.get_board_data()
            actual_elapsed = time.perf_counter() - window_start
            with self._lock:
                self._window_durations.append(actual_elapsed)

            if self._stop_event.is_set():
                break

            if data.shape[1] == 0:
                log_info("EEG WARN", f"W{self._window_index:04d} 0 samples")
                self._window_index += 1
                continue

            if not self._pause_event.is_set() and not self._save_while_paused:
                self.board_shim.get_board_data()
                continue

            validate_eeg_chunk(
                data, self.eeg_row_indices, self.fs,
                self.window_duration, self._window_index,
            )

            if self._stop_event.is_set():
                break

            expected = int(round(self.fs * self.window_duration))
            idx = self._window_index
            show = EEG_DEBUG or EEG_VERBOSE or (idx % EEG_LOG_EVERY == 0) or idx < 2
            if show:
                ok = "OK" if abs(data.shape[1] - expected) <= expected * 0.2 else "!"
                print(
                    f"  [EEG] #{idx:04d} | {data.shape[0]}x{data.shape[1]} | "
                    f"{data.shape[1]:3d}/{expected} smp | {actual_elapsed*1000:5.0f} ms | {ok}"
                )
            try:
                data_copy  = data.copy()
                block_name = f"{self.participant_id}_w{idx:04d}_raw"
                _process_and_save_window(
                    data_copy, self.board_id, block_name,
                    self.recording_dir, self.participant_id,
                )
            except Exception as exc:
                log_info("EEG ERR", f"W{idx:04d} save failed: {exc}")
            if self._stop_event.is_set():
                break
            self._data_queue.put(data.copy())
            for sub_q in self._subscribers:
                try:
                    sub_q.put_nowait(data.copy())
                except Exception:
                    pass
            self._window_index += 1


def shutdown_experiment():
    """Stop EEG thread first, then visualizer and BrainFlow."""
    global _quitting
    _quitting = True
    ctrl = _run_handles.get("eeg_controller")
    vis = _run_handles.get("visualizer")
    board = _run_handles.get("board_shim")
    if ctrl is not None:
        try:
            ctrl.stop()
        except Exception:
            pass
    if vis is not None:
        try:
            vis.stop()
        except Exception:
            pass
    if board is not None:
        try:
            if board.is_prepared():
                board.stop_stream()
                board.release_session()
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
    # Older BrainFlow: no disable_dev_board_logger — board logs may still print (harmless)

    #brainflow initialization 
    params = BrainFlowInputParams()
    params.serial_number = "UN-2023.08.11"
    # params.serial_port = serial_port
    board_shim = BoardShim(BOARD_ID, params)

    #prepare board
    try:
        board_shim.prepare_session()
    except brainflow.board_shim.BrainFlowError as e:
        print(f"Error: {e}")
        print("The end")
        time.sleep(1)
        sys.exit()
    #board start streaming
    board_shim.start_stream()

    log_banner("BCI Speller + EEG stream")
    fs, eeg_rows = print_board_layout(board_shim, BOARD_ID, EEG_WINDOW_SEC, 8)
    log_section("Controls")
    log_info("Quit", "Focus board window -> Esc or Q | or Ctrl+C in terminal")
    log_info("EEG window", f"{EEG_WINDOW_SEC}s (set EEG_WINDOW_SEC=1.0 for supervisor demo)")
    log_info("Verbose EEG", f"EEG_VERBOSE=1 all windows | default log every {EEG_LOG_EVERY}")
    logging.info("Begining the experiment")

    eeg_controller = EEGStreamController(
        board_shim        = board_shim,
        window_duration   = EEG_WINDOW_SEC,
        board_id          = BOARD_ID,
        recording_dir     = RECORDING_DIR,
        participant_id    = PARTICIPANT_ID,
        eeg_row_indices   = eeg_rows,
    )
    _run_handles["board_shim"] = board_shim
    _run_handles["eeg_controller"] = eeg_controller

    visualizer = EEGVisualizer(
        board_shim      = board_shim,
        board_id        = BOARD_ID,
        n_channels      = 8,
        window_sec      = 5,
        plot_hz         = 20,
        amplitude_uv    = 100,
        monitor_index   = VISUALIZER_MONITOR if DEV_DUAL_MONITOR else 0,
    )
    eeg_controller.add_subscriber(visualizer.data_queue)
    _run_handles["visualizer"] = visualizer

    while True:

        # Starting the display
        trialClock = core.Clock()
        cal_start.draw()
        window.flip()
        if wait_seconds(3):
            break

        drawTextOnScreen(f"Hi {PARTICIPANT_NAME}.\nStarting the experiment.Please do not move now\nBoard ID: {BOARD_ID}",window)
        if wait_seconds(10):
            break

        eeg_controller.start()
        visualizer.start()
        if DEV_DUAL_MONITOR:
            if wait_seconds(1.5):
                break
        sequence = random.sample(TARGET_CHARACTERS, len(TARGET_CHARACTERS))

        for block in range(NUM_BLOCK):
            for trials in range(NUM_TRIAL):
                get_keypress()
                # Drawing display box

                # Drawing the grid
                # Display target characters
                for target in targets.values():
                    target.autoDraw = True
                    # get_keypress()
                flicker(board_shim)

                # At the end of the trial, calculate real duration and amount of frames
                t1 = trialClock.getTime()  # Time at end of trial
                elapsed = t1 - t0
                print(f"Time elapsed: {elapsed}")
                print(f"Total frames: {frames}")

                for target in targets.values():
                    target.autoDraw = False
                    ###
                eeg_controller.pause()
                visualizer.pause()
                countdown_timer = core.CountdownTimer(TRIAL_BREAK)
                if (trials + 1) < NUM_TRIAL: 
                    # drawTextOnScreen('trials Break 30 sec. You can blink but please donot move.',window)
                    # core.wait(BLOCK_BREAK)
                    trial_break_start.autoDraw = True
                    while countdown_timer.getTime() > 0:
                        if check_escape():
                            break
                        time_remaining = countdown_timer.getTime()
                        counter.text = f'Block {int(block+1)}/{int(NUM_BLOCK)}. End of trial {int(trials+1)}.\n {int(NUM_TRIAL- (trials+1))} trial(s) left for this block.\nTime remaining: {int(time_remaining)}'
                        counter.draw()
                        window.flip()

                # trials += 1
                trial_break_start.autoDraw = False
                ###
                eeg_controller.resume()
                visualizer.resume()
                window.flip()

            for target in targets.values():
                target.autoDraw = False
            eeg_controller.pause()
            visualizer.pause()
            countdown_timer = core.CountdownTimer(BLOCK_BREAK)
            if (block + 1) < NUM_BLOCK: 
                # drawTextOnScreen('Block Break 30 sec. You can blink but please donot move.',window)
                # core.wait(BLOCK_BREAK)
                block_break_start.autoDraw = True
                while countdown_timer.getTime() > 0:
                    if check_escape():
                        break
                    time_remaining = countdown_timer.getTime()
                    counter.text = f'End of block {int(block+1)}.\n {int(NUM_BLOCK - (block+1))} block(s) left.\n Time remaining: {int(time_remaining)}'
                    counter.draw()
                    window.flip()

            # block += 1
            block_break_start.autoDraw = False
            ###
            eeg_controller.resume()
            visualizer.resume()
            window.flip()

        
        #Adding buffer of 10 sec at the end
        if wait_seconds(10):
            break
        eeg_controller.stop()
        eeg_controller.print_stats()
        visualizer.stop()
###
        # saving the data from 1 block
        block_name = f'{PARTICIPANT_ID}_raw'
        data = board_shim.get_board_data()
        data_copy = data.copy()
        _process_and_save_window(data_copy, BOARD_ID, block_name, RECORDING_DIR, PARTICIPANT_ID)
        # save_csv(data, RECORDING_DIR, PARTICIPANT_ID)
        drawTextOnScreen('End of experiment, Thank you',window)
        wait_seconds(3)
        break


    if board_shim.is_prepared():
        logging.info('Releasing session')
        # stop board to stream
        board_shim.stop_stream()
        board_shim.release_session()

    #cleanup
    window.close()
    core.quit()




if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()