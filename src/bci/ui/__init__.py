"""User-facing BCI applications."""

from bci.ui.signal_monitor.app import SignalMonitorApp
from bci.ui.ssvep.app import SSVEPStimulusApp

__all__ = ["SignalMonitorApp", "SSVEPStimulusApp"]
