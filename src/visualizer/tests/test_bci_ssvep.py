"""Tests for bci.ui.ssvep stimulus and application."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from bci.ui.ssvep.stimulus import Target, generate_3x3_grid
from bci.ui.ssvep.app import SSVEPStimulusApp, load_config_json, hex_to_rgb


def test_target_dataclass() -> None:
    target = Target(position=(0.1, 0.2), frequency=10.5, pattern="sine", label="X")
    assert target.position == (0.1, 0.2)
    assert target.frequency == 10.5
    assert target.pattern == "sine"
    assert target.label == "X"


def test_target_draw() -> None:
    target = Target(position=(0, 0), frequency=10.0, pattern="sine", label="A")
    target.rect = MagicMock()
    target.text = MagicMock()
    target.draw()
    target.rect.draw.assert_called_once()
    target.text.draw.assert_called_once()


@patch("psychopy.visual.TextStim")
@patch("psychopy.visual.Rect")
def test_target_init_with_win(mock_rect: MagicMock, mock_text: MagicMock) -> None:
    win = MagicMock()
    target = Target(position=(0, 0), frequency=10.0, pattern="sine", label="A", win=win)
    assert target.rect is not None
    assert target.text is not None


def test_hex_to_rgb() -> None:
    assert hex_to_rgb("#FFFFFF") == (1.0, 1.0, 1.0)
    assert hex_to_rgb("#000000") == (-1.0, -1.0, -1.0)
    assert hex_to_rgb("#FFF") == (1.0, 1.0, 1.0)


def test_generate_grid_defaults() -> None:
    targets = generate_3x3_grid()
    assert len(targets) == 9
    assert targets[0].frequency == 8.0
    assert targets[8].frequency == 9.6
    assert targets[0].label == "A"
    assert targets[0].position == (-800, 300)
    assert targets[0].pattern == "square-wave"


def test_generate_grid_custom_config() -> None:
    config = {
        "frequencies": [10.0, 11.0],
        "labels": ["1", "2"],
        "flicker_method": "sine",
        "positions": [(0.4, 0.4), (0.6, 0.6)],
    }
    targets = generate_3x3_grid(config)
    assert len(targets) == 2
    assert targets[0].frequency == 10.0
    assert targets[0].label == "1"
    assert targets[0].position == (0.4, 0.4)
    assert targets[0].pattern == "sine"


def test_ssvep_app_initialization() -> None:
    config = {
        "plot_hz": 30,
        "color_on": "#FFFFFF",
        "color_off": "#000000",
        "target_width_pixels": 200,
        "target_height_pixels": 200,
    }
    app = SSVEPStimulusApp(config)
    assert app.plot_hz == 30
    assert app.color_on == "#FFFFFF"
    assert app.color_off == "#000000"
    assert app.target_width == 200
    assert app.target_height == 200
    assert len(app.targets) == 9
    assert app.is_running is False


@patch("psychopy.visual.TextStim")
@patch("psychopy.visual.Rect")
@patch("psychopy.visual.Window")
@patch("psychopy.event.getKeys")
def test_ssvep_app_start(
    mock_get_keys: MagicMock,
    mock_window: MagicMock,
    mock_rect: MagicMock,
    mock_text: MagicMock,
) -> None:
    mock_get_keys.return_value = ["escape"]
    
    app = SSVEPStimulusApp()
    app.start()
    
    assert mock_window.called
    assert not app.is_running


def test_load_config_json(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    data = {"frequencies": [9.0, 9.5], "flicker_method": "sine"}
    config_file.write_text(json.dumps(data))

    config = load_config_json(str(config_file))
    assert config["frequencies"] == [9.0, 9.5]
    assert config["flicker_method"] == "sine"

    # Non-existent file should safely return empty dict
    bad_config = load_config_json("does_not_exist.json")
    assert bad_config == {}


def test_get_screen_resolution() -> None:
    from bci.ui.ssvep.app import _get_screen_resolution
    with patch("platform.system", return_value="Windows"), \
         patch("win32api.GetSystemMetrics", side_effect=[1920, 1080]):
        assert _get_screen_resolution() == (1920, 1080)

    with patch("platform.system", return_value="Linux"):
        assert _get_screen_resolution() == (1920, 1080)


def test_ssvep_app_speller_config_fallbacks() -> None:
    # Force ImportError on direct speller_config import, and verify fallback behavior
    import sys
    
    # Save existing modules
    saved_speller_config = sys.modules.get("speller_config")
    saved_visualizer_speller_config = sys.modules.get("visualizer.speller_config")
    
    sys.modules["speller_config"] = None
    sys.modules["visualizer.speller_config"] = None
    
    try:
        app = SSVEPStimulusApp()
        # Fallback width/height defaults
        assert app.target_width == 100.0
    finally:
        # Restore sys.modules
        if saved_speller_config is not None:
            sys.modules["speller_config"] = saved_speller_config  # pragma: no cover
        else:
            sys.modules.pop("speller_config", None)
            
        if saved_visualizer_speller_config is not None:
            sys.modules["visualizer.speller_config"] = saved_visualizer_speller_config  # pragma: no cover
        else:
            sys.modules.pop("visualizer.speller_config", None)  # pragma: no cover
