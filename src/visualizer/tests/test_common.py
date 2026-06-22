import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import numpy as np

from visualizer.utils.common import (
    create_session_folder, getdata, getdata_offline, 
    save_raw, save_ssvep_raw, save_raw_to_dataframe, 
    drawTextOnScreen, save_csv
)


@patch('visualizer.utils.common.os.getcwd', return_value='C:\\mock_dir')
@patch('visualizer.utils.common.os.path.isdir', return_value=False)
@patch('visualizer.utils.common.os.makedirs')
def test_create_session_folder_new(mock_makedirs, mock_isdir, mock_getcwd):
    path = create_session_folder('subj1', 'logs')
    assert 'subj1' in path
    mock_makedirs.assert_called_once()

@patch('visualizer.utils.common.os.getcwd', return_value='C:\\mock_dir')
@patch('visualizer.utils.common.os.path.isdir', return_value=True)
@patch('visualizer.utils.common.os.makedirs')
def test_create_session_folder_existing(mock_makedirs, mock_isdir, mock_getcwd):
    path = create_session_folder('subj1', 'logs')
    assert 'subj1' in path
    mock_makedirs.assert_not_called()

@patch('visualizer.utils.common.BoardShim')
@patch('visualizer.utils.common.mne')
@patch('visualizer.utils.common.eegbci')
def test_getdata(mock_eegbci, mock_mne, mock_boardshim):
    mock_boardshim.get_marker_channel.return_value = 8
    mock_boardshim.get_eeg_channels.return_value = [0, 1, 2, 3]
    mock_boardshim.get_eeg_names.return_value = ['ch1', 'ch2', 'ch3', 'ch4']
    mock_boardshim.get_sampling_rate.return_value = 250
    
    mock_raw = MagicMock()
    mock_mne.io.RawArray.return_value = mock_raw
    mock_raw.copy.return_value = mock_raw
    mock_raw.notch_filter.return_value = mock_raw
    mock_raw.filter.return_value = mock_raw
    
    data = np.ones((10, 100))
    board = MagicMock()
    
    res = getdata(data, board, dropEnable=True)
    assert res == mock_raw

@patch('visualizer.utils.common.BoardShim')
@patch('visualizer.utils.common.mne')
@patch('visualizer.utils.common.eegbci')
def test_getdata_offline(mock_eegbci, mock_mne, mock_boardshim):
    mock_boardshim.get_marker_channel.return_value = 8
    mock_boardshim.get_eeg_channels.return_value = [0, 1, 2, 3]
    mock_boardshim.get_eeg_names.return_value = ['ch1', 'ch2', 'ch3', 'ch4']
    mock_boardshim.get_sampling_rate.return_value = 250
    
    mock_raw = MagicMock()
    mock_mne.io.RawArray.return_value = mock_raw
    mock_raw.copy.return_value = mock_raw
    
    data = np.ones((10, 100))
    board = MagicMock()
    
    res = getdata_offline(data, board, dropEnable=True)
    assert res == mock_raw

@patch('visualizer.utils.common.create_session_folder', return_value='mock_folder')
@patch('visualizer.utils.common.os.path.basename', return_value='mock_folder')
def test_save_raw(mock_basename, mock_create):
    raw = MagicMock()
    res = save_raw(raw, 'test', 'logs', 'subj1')
    assert res == 'mock_folder'
    raw.save.assert_called_once()

@patch('visualizer.utils.common.create_session_folder', return_value='mock_folder')
@patch('visualizer.utils.common.os.path.basename', return_value='mock_folder')
def test_save_ssvep_raw(mock_basename, mock_create):
    raw = MagicMock()
    res = save_ssvep_raw(raw, 'test', 'logs')
    assert res == 'mock_folder'
    raw.save.assert_called_once()

@patch('visualizer.utils.common.create_session_folder', return_value='mock_folder')
@patch('visualizer.utils.common.PARTICIPANT_ID', 'test_id', create=True)
@patch('visualizer.utils.common.CSV_DIR', 'test_dir', create=True)
def test_save_raw_to_dataframe(mock_create):
    raw = MagicMock()
    df = MagicMock()
    raw.copy.return_value.to_data_frame.return_value = df
    save_raw_to_dataframe(raw, 'test')
    df.to_csv.assert_called_once()

@patch('visualizer.utils.common.visual.TextStim')
def test_drawTextOnScreen(mock_text_stim):
    window = MagicMock()
    drawTextOnScreen("hello", window)
    mock_text_stim.assert_called_once_with(window, text="hello", color=(-1., -1., -1.))
    mock_text_stim.return_value.draw.assert_called_once()
    window.flip.assert_called_once()

@patch('visualizer.utils.common.create_session_folder', return_value='mock_folder')
@patch('builtins.open', new_callable=mock_open)
@patch('visualizer.utils.common.pickle.dump')
def test_save_csv(mock_dump, mock_file, mock_create):
    save_csv({'a': 1}, 'test', 'logs', 'subj1')
    mock_dump.assert_called_once()
