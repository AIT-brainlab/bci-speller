"""Magic number constants for the EEG visualizer."""

from __future__ import annotations

# Queue sizes
DATA_QUEUE_MAXSIZE = 300
MARKER_QUEUE_MAXSIZE = 100

# Geometry
GEOMETRY_MARGIN = 48  # pixels

# Timeouts (seconds)
PROCESS_JOIN_TIMEOUT = 5.0
FEEDER_TIMEOUT = 2.0
AFTER_TIMEOUT = 0.8

# Polling
POLL_INTERVAL_SEC = 0.05
