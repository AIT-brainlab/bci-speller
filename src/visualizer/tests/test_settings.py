"""Tests for configuration loading."""

from __future__ import annotations

import pytest

from visualizer.config.exceptions import VisualizerConfigError
from visualizer.config.settings import (
    get_visualizer_settings,
    resolve_plot_params,
)


def test_get_settings_missing_env(clean_settings_cache) -> None:
    with pytest.raises(VisualizerConfigError) as exc:
        get_visualizer_settings()
    assert "EEG_VIS_WINDOW_SEC" in str(exc.value)


def test_resolve_without_env_or_args(clean_settings_cache) -> None:
    with pytest.raises(VisualizerConfigError):
        resolve_plot_params()


def test_format_validation_error_non_pydantic() -> None:
    from visualizer.config.settings import _format_validation_error

    text = _format_validation_error(RuntimeError("boom"))
    assert "boom" in text


def test_get_settings_success(visualizer_env: None) -> None:
    settings = get_visualizer_settings()
    assert settings.window_sec == 5.0
    assert settings.plot_hz == 20
    assert settings.amplitude_uv == 100.0


def test_resolve_all_from_constructor() -> None:
    w, p, a = resolve_plot_params(window_sec=3.0, plot_hz=10, amplitude_uv=50.0)
    assert (w, p, a) == (3.0, 10, 50.0)


def test_resolve_from_env(visualizer_env: None) -> None:
    w, p, a = resolve_plot_params()
    assert (w, p, a) == (5.0, 20, 100.0)


def test_resolve_partial_requires_env(visualizer_env: None) -> None:
    w, p, a = resolve_plot_params(window_sec=7.0)
    assert w == 7.0
    assert p == 20
    assert a == 100.0


def test_resolve_invalid_positive() -> None:
    with pytest.raises(VisualizerConfigError):
        resolve_plot_params(window_sec=0, plot_hz=1, amplitude_uv=1)


def test_settings_field_validators() -> None:
    from visualizer.config.settings import VisualizerSettings

    with pytest.raises(Exception):
        VisualizerSettings(window_sec=-1, plot_hz=1, amplitude_uv=1)
    with pytest.raises(Exception):
        VisualizerSettings(window_sec=1, plot_hz=0, amplitude_uv=1)


def test_resolve_partial_when_env_incomplete(clean_settings_cache,monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EEG_VIS_WINDOW_SEC", "5")
    from visualizer.config.settings import get_visualizer_settings

    get_visualizer_settings.cache_clear()
    with pytest.raises(VisualizerConfigError) as exc:
        resolve_plot_params(window_sec=7.0)
    assert "amplitude_uv" in str(exc.value) or "plot_hz" in str(exc.value)


def test_settings_rejects_bad_values(visualizer_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EEG_VIS_PLOT_HZ", "-1")
    from visualizer.config.settings import get_visualizer_settings

    get_visualizer_settings.cache_clear()
    with pytest.raises(VisualizerConfigError):
        get_visualizer_settings()
