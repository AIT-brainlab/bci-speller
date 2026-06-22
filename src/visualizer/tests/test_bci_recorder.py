"""Tests for bci.recorder.fif module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
import numpy as np

from bci.recorder.fif import FifRecorder


def test_fif_recorder_verbose_true() -> None:
    recorder = FifRecorder(
        board_id=8,
        recording_dir="test_dir_verbose",
        participant_id="subj_verbose",
        fs=250.0,
        verbose=True,
    )
    
    with patch("bci.recorder.fif.getdata_offline") as mock_getdata, \
         patch("bci.recorder.fif.save_raw") as mock_save_raw:
        
        recorder.start()
        chunk = np.ones((8, 125))
        recorder.stream.put(chunk)
        time.sleep(0.15)  # wait for thread loop to consume
        
        # Test pause (should not append to all_chunks or save)
        recorder.pause()
        chunk_paused = np.ones((8, 125))
        recorder.stream.put(chunk_paused)
        time.sleep(0.15)
        
        # Resume
        recorder.resume()
        chunk_resumed = np.ones((8, 125))
        recorder.stream.put(chunk_resumed)
        time.sleep(0.15)
        
        recorder.save_full_block("full_block_verbose")
        recorder.print_stats()
        
        recorder.stop()
        
        # Verify that getdata_offline and save_raw were called
        assert mock_getdata.called
        assert mock_save_raw.called


def test_fif_recorder_verbose_false() -> None:
    recorder = FifRecorder(
        board_id=8,
        recording_dir="test_dir_quiet",
        participant_id="subj_quiet",
        fs=250.0,
        verbose=False,
    )
    
    with patch("bci.recorder.fif.getdata_offline") as mock_getdata, \
         patch("bci.recorder.fif.save_raw") as mock_save_raw:
        
        recorder.start()
        chunk = np.ones((8, 125))
        recorder.stream.put(chunk)
        time.sleep(0.15)
        
        recorder.stop()
        
        assert mock_getdata.called
        assert mock_save_raw.called


def test_fif_recorder_empty_save_and_stats() -> None:
    recorder = FifRecorder(
        board_id=8,
        recording_dir="test_dir_empty",
        participant_id="subj_empty",
    )
    recorder.save_full_block("empty_block")
    recorder.print_stats()


def test_fif_recorder_exceptions() -> None:
    recorder = FifRecorder(
        board_id=8,
        recording_dir="test_dir_err",
        participant_id="subj_err",
    )
    
    # Mock save_raw to throw an exception
    with patch("bci.recorder.fif.save_raw", side_effect=Exception("mock write fail")), \
         patch("bci.recorder.fif.getdata_offline"):
        # Write exception (verbose=True)
        recorder.verbose = True
        recorder.write(np.ones((8, 125)))
        
        # Write exception (verbose=False, triggering redirect and mne exception)
        recorder.verbose = False
        with patch("mne.set_log_level", side_effect=Exception("mne fail")):
            recorder.write(np.ones((8, 125)))

        # save_full_block exception
        recorder._all_chunks = [np.ones((8, 125))]
        recorder.save_full_block("full_block_err")
