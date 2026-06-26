"""Live EEG signal monitor UI."""

from bci.ui.signal_monitor.app import SignalMonitorApp
from bci.ui.signal_monitor.process import run_signal_monitor_process

__all__ = ["SignalMonitorApp", "run_signal_monitor_process"]
