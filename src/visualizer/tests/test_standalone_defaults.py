"""Cover standalone default board id / serial helpers."""

from __future__ import annotations

import os
from unittest.mock import patch

from visualizer.standalone import _default_board_id, _default_serial


def test_default_serial_from_env(monkeypatch) -> None:
    monkeypatch.setenv("BRAINFLOW_SERIAL", "TEST-SERIAL")
    assert _default_serial() == "TEST-SERIAL"


def test_default_board_id_from_env(monkeypatch) -> None:
    monkeypatch.setenv("BOARD_ID", "42")
    assert _default_board_id() == 42


@patch.dict(os.environ, {}, clear=True)
def test_default_board_id_fallback() -> None:
    assert isinstance(_default_board_id(), int)
