"""Tests for bci.ui.ssvep stimulus and application."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from bci.ui.ssvep.stimulus import Target, generate_3x3_grid
from bci.ui.ssvep.app import SSVEPStimulusApp, load_config_json


def test_target_dataclass() -> None:
    target = Target(position=(0.1, 0.2), frequency=10.5, pattern="sine", label="X")
    assert target.position == (0.1, 0.2)
    assert target.frequency == 10.5
    assert target.pattern == "sine"
    assert target.label == "X"


def test_generate_grid_defaults() -> None:
    targets = generate_3x3_grid()
    assert len(targets) == 9
    assert targets[0].frequency == 8.0
    assert targets[8].frequency == 16.0
    assert targets[0].label == "A"
    assert targets[0].position == (0.2, 0.8)
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


@patch("matplotlib.pyplot.show")
@patch("matplotlib.pyplot.subplots")
def test_ssvep_app_start(mock_subplots: MagicMock, mock_show: MagicMock) -> None:
    fig = MagicMock()
    ax = MagicMock()
    mock_subplots.return_value = (fig, ax)

    app = SSVEPStimulusApp()
    app.start()

    assert mock_subplots.called
    assert mock_show.called
    assert app.is_running is False  # becomes False after show exits


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
