"""Cover standalone helper fallbacks."""

from __future__ import annotations

import builtins
from unittest.mock import patch

from visualizer import standalone as standalone_mod


def test_default_board_id_import_fallback() -> None:
    real_import = builtins.__import__

    def _import(name: str, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "visualizer.speller_config":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=_import):
        assert standalone_mod._default_board_id() == 8
        assert __import__("math") is not None

