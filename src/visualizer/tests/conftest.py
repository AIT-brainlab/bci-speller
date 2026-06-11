"""Shared pytest fixtures."""

from __future__ import annotations

import os
import sys
from types import ModuleType
from typing import Any, Generator
from pathlib import Path
import pytest


def _install_fake_brainflow() -> None:
    """Allow tests without the real brainflow wheel installed."""
    if "brainflow.board_shim" in sys.modules:
        return

    brainflow = ModuleType("brainflow")
    board_shim_mod = ModuleType("brainflow.board_shim")

    class BrainFlowInputParams:
        def __init__(self) -> None:
            self.serial_number: str = ""

    class BoardShim:
        def __init__(self, board_id: int, params: Any) -> None:
            self.board_id = board_id
            self.params = params

        @staticmethod
        def get_sampling_rate(board_id: int) -> int:
            return 250

        @staticmethod
        def get_eeg_channels(board_id: int) -> list[int]:
            return list(range(1, 9))

        def prepare_session(self) -> None:
            pass

        def start_stream(self) -> None:
            pass

        def get_board_data(self) -> Any:
            return None

        def is_prepared(self) -> bool:
            return True

        def stop_stream(self) -> None:
            pass

        def release_session(self) -> None:
            pass

    board_shim_mod.BoardShim = BoardShim
    board_shim_mod.BrainFlowInputParams = BrainFlowInputParams
    brainflow.board_shim = board_shim_mod
    sys.modules["brainflow"] = brainflow
    sys.modules["brainflow.board_shim"] = board_shim_mod


_install_fake_brainflow()


@pytest.fixture(autouse=True)
def _headless_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent Tk/matplotlib windows during tests."""
    monkeypatch.setenv("MPLBACKEND", "Agg")


@pytest.fixture(autouse=True)
def _clear_visualizer_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Avoid leaking EEG_VIS_* between tests."""
    for key in list(os.environ):
        if key.startswith("EEG_VIS_"):
            monkeypatch.delenv(key, raising=False)
    from visualizer.config.settings import get_visualizer_settings

    get_visualizer_settings.cache_clear()
    yield
    get_visualizer_settings.cache_clear()


@pytest.fixture
def visualizer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EEG_VIS_WINDOW_SEC", "5")
    monkeypatch.setenv("EEG_VIS_PLOT_HZ", "20")
    monkeypatch.setenv("EEG_VIS_AMPLITUDE_UV", "100")
    from visualizer.config.settings import get_visualizer_settings

    get_visualizer_settings.cache_clear()

@pytest.fixture
def clean_settings_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[None, None, None]:
    """Clear lru_cache and block .env so settings tests start fresh."""
    from pydantic_settings import SettingsConfigDict

    from visualizer.config.settings import VisualizerSettings, get_visualizer_settings

    missing_env = tmp_path / "missing.env"
    monkeypatch.setattr(
        VisualizerSettings,
        "model_config",
        SettingsConfigDict(
            env_file=str(missing_env),
            env_file_encoding="utf-8",
            env_prefix="EEG_VIS_",
            extra="ignore",
            populate_by_name=True,
        ),
    )
    for key in ("EEG_VIS_WINDOW_SEC", "EEG_VIS_PLOT_HZ", "EEG_VIS_AMPLITUDE_UV"):
        monkeypatch.delenv(key, raising=False)
    get_visualizer_settings.cache_clear()
    yield
    get_visualizer_settings.cache_clear()