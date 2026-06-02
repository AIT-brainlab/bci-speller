"""Cover test fixture helper branches that are otherwise not exercised."""

from __future__ import annotations

import os
import sys
from types import ModuleType

import pytest

from .conftest import _install_fake_brainflow

os.environ.setdefault("EEG_VIS_FIXTURE_COVERAGE", "1")


def test_install_fake_brainflow_returns_when_already_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    brainflow = ModuleType("brainflow")
    board_shim_mod = ModuleType("brainflow.board_shim")
    brainflow.board_shim = board_shim_mod
    monkeypatch.setitem(sys.modules, "brainflow", brainflow)
    monkeypatch.setitem(sys.modules, "brainflow.board_shim", board_shim_mod)

    _install_fake_brainflow()


def test_fake_brainflow_boardshim_methods_are_callable() -> None:
    import brainflow.board_shim as bf

    params = bf.BrainFlowInputParams()
    board = bf.BoardShim(1, params)

    assert board.board_id == 1
    assert board.params is params
    board.prepare_session()
    board.start_stream()
    assert board.get_board_data() is None
    assert board.is_prepared() is True
    board.stop_stream()
    board.release_session()


def test_autouse_fixture_removes_eeg_vis_environment_variable() -> None:
    assert "EEG_VIS_FIXTURE_COVERAGE" not in os.environ
