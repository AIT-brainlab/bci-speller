"""Load required plot settings from environment variables (see .env.example)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from visualizer.config.exceptions import VisualizerConfigError

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ENV_FILE = _PACKAGE_ROOT / ".env"

_MISSING_ENV_HELP = """
╔══════════════════════════════════════════════════════════════════╗
║  EEG Visualizer — required configuration missing                 ║
╠══════════════════════════════════════════════════════════════════╣
║  Set these environment variables (or copy .env.example → .env):  ║
║                                                                  ║
║    EEG_VIS_WINDOW_SEC     Rolling plot window (seconds)          ║
║    EEG_VIS_PLOT_HZ        UI refresh rate (frames per second)    ║
║    EEG_VIS_AMPLITUDE_UV   Y-axis half-range (microvolts)         ║
║                                                                  ║
║  Example (.env in the visualizer/ folder):                       ║
║    EEG_VIS_WINDOW_SEC=5                                          ║
║    EEG_VIS_PLOT_HZ=20                                            ║
║    EEG_VIS_AMPLITUDE_UV=100                                      ║
║                                                                  ║
║  Or pass window_sec, plot_hz, amplitude_uv to EEGVisualizer().   ║
╚══════════════════════════════════════════════════════════════════╝
"""


class VisualizerSettings(BaseSettings):
    """Required plot parameters (env prefix EEG_VIS_)."""

    model_config = SettingsConfigDict(
        env_file=str(_DEFAULT_ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="EEG_VIS_",
        extra="ignore",
        populate_by_name=True,
    )

    window_sec: float = Field(..., description="Rolling plot window length in seconds")
    plot_hz: int = Field(..., description="Matplotlib animation refresh rate")
    amplitude_uv: float = Field(..., description="Half-range of the Y axis in µV")

    @field_validator("window_sec", "amplitude_uv")
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("plot_hz")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value


def _format_validation_error(exc: Exception) -> str:
    lines = [_MISSING_ENV_HELP.strip(), "", "Details:"]
    if hasattr(exc, "errors"):
        for err in exc.errors():  # type: ignore[attr-defined]
            loc = ".".join(str(part) for part in err.get("loc", ()))
            msg = err.get("msg", "invalid")
            env_key = f"EEG_VIS_{loc.upper()}" if loc else "EEG_VIS_*"
            lines.append(f"  • {env_key}: {msg}")
    else:
        lines.append(f"  • {exc}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def get_visualizer_settings() -> VisualizerSettings:
    """Load settings from .env / environment. Cached after first successful load."""
    try:
        return VisualizerSettings()
    except Exception as exc:
        raise VisualizerConfigError(_format_validation_error(exc)) from exc


def resolve_plot_params(
    window_sec: Optional[float] = None,
    plot_hz: Optional[int] = None,
    amplitude_uv: Optional[float] = None,
) -> tuple[float, int, float]:
    """
    Resolve plot parameters from explicit arguments or environment.

    Raises VisualizerConfigError if any value is still missing.
    """
    if window_sec is not None and plot_hz is not None and amplitude_uv is not None:
        w, p, a = float(window_sec), int(plot_hz), float(amplitude_uv)
    else:
        try:
            settings = get_visualizer_settings()
        except VisualizerConfigError:
            if window_sec is None and plot_hz is None and amplitude_uv is None:
                raise
            settings = None

        if settings is None:
            missing = [
                name
                for name, value in (
                    ("window_sec", window_sec),
                    ("plot_hz", plot_hz),
                    ("amplitude_uv", amplitude_uv),
                )
                if value is None
            ]
            raise VisualizerConfigError(
                _MISSING_ENV_HELP.strip()
                + "\n\nStill missing: "
                + ", ".join(missing)
                + " (set EEG_VIS_* env vars or pass them to EEGVisualizer)."
            )

        w = float(window_sec) if window_sec is not None else settings.window_sec
        p = int(plot_hz) if plot_hz is not None else settings.plot_hz
        a = float(amplitude_uv) if amplitude_uv is not None else settings.amplitude_uv

    if w <= 0 or a <= 0 or p <= 0:
        raise VisualizerConfigError("window_sec, plot_hz, and amplitude_uv must be > 0.")

    return w, p, a
