# Deprecated — superseded by `bci` package

The original `visualizer` module is being replaced by the refactored layout:

| Old location | New location |
|---|---|
| `stream_feeder.py` | `src/bci/board/streaming.py` + `brainflow_board.py` |
| `process.py` (GUI) | `src/bci/ui/signal_monitor/app.py` |
| `monitor.py` (window placement) | `src/bci/ui/signal_monitor/widgets.py` |
| `theme.py` | `src/bci/ui/signal_monitor/widgets.py` |
| `standalone.py` (board wiring) | `scripts/run_signal_monitor.py` |

**New entry points:**

```bash
# Board-only test (no GUI)
python scripts/test_board_standalone.py

# Full signal monitor with synthetic board
python scripts/run_signal_monitor.py
```

The legacy `visualizer` package remains for backward compatibility with existing
experiments and tests. Remove once all consumers migrate to `bci`.
