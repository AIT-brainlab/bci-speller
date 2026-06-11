"""Configuration for the EEG visualizer (Pydantic + ``EEG_VIS_*`` env vars)."""

from visualizer.config.constants import (
    AFTER_TIMEOUT,
    DATA_QUEUE_MAXSIZE,
    FEEDER_TIMEOUT,
    GEOMETRY_MARGIN,
    MARKER_QUEUE_MAXSIZE,
    POLL_INTERVAL_SEC,
    PROCESS_JOIN_TIMEOUT,
)
from visualizer.config.exceptions import VisualizerConfigError
from visualizer.config.settings import (
    VisualizerSettings,
    get_visualizer_settings,
    resolve_plot_params,
)

__all__ = [
    "VisualizerConfigError",
    "VisualizerSettings",
    "get_visualizer_settings",
    "resolve_plot_params",
    "DATA_QUEUE_MAXSIZE",
    "MARKER_QUEUE_MAXSIZE",
    "GEOMETRY_MARGIN",
    "PROCESS_JOIN_TIMEOUT",
    "FEEDER_TIMEOUT",
    "AFTER_TIMEOUT",
    "POLL_INTERVAL_SEC",
]
