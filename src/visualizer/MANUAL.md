# EEG Visualizer — Maintainer Manual

## Purpose

The visualizer shows rolling EEG traces while data is collected. Code is split so that:

1. **`EEGVisualizer`** lives in `live_monitor_class.py` for reuse.
2. **`python -m visualizer`** runs without `experiment.py` / PsychoPy.
3. Plot tuning uses **environment variables** (`EEG_VIS_*`) or constructor args, with clear errors when unset.

## Architecture

```
┌─────────────────────┐     put(copy)      ┌──────────────────────────┐
│ EEGStreamController │ ─────────────────► │ multiprocessing.Queue    │
│ (experiment thread) │                    │ visualizer.data_queue    │
└─────────────────────┘                    └────────────┬─────────────┘
                                                      │
┌─────────────────────┐     put(copy)               │
│ BoardStreamFeeder     │ ────────────────────────────┘
│ (standalone thread) │
└─────────────────────┘
                                                      ▼
                                            ┌──────────────────────────┐
                                            │ EEGVisualizer Process    │
                                            │ run_visualizer_process() │
                                            │ TkAgg + matplotlib       │
                                            └──────────────────────────┘
```

**Rules**

- The child process **never** calls `board_shim.get_board_data()`.
- Only the parent (experiment or feeder) pushes numpy arrays into `data_queue`.
- Matplotlib is imported **only** inside `process.run_visualizer_process()` for Windows `spawn` safety.

## Configuration

### Required plot parameters

| Env variable | Constructor kwarg | Description |
|--------------|-------------------|-------------|
| `EEG_VIS_WINDOW_SEC` | `window_sec` | Seconds of signal on screen |
| `EEG_VIS_PLOT_HZ` | `plot_hz` | Animation interval = 1000/plot_hz ms |
| `EEG_VIS_AMPLITUDE_UV` | `amplitude_uv` | ± range on Y axis (µV) |

**Priority:** constructor arguments override `.env` / environment.

**Failure mode:** `VisualizerConfigError` with a visible ASCII box and field hints.

Implementation: `config/settings.py` (`VisualizerSettings`, `resolve_plot_params`).

### Optional runtime

| Variable | Used by |
|----------|---------|
| `BOARD_ID` | Standalone board id |
| `BRAINFLOW_SERIAL` | Standalone serial |
| `VISUALIZER_MONITOR` | Monitor index for plot window |

Theme colors and default channel names live in `theme.py` (not env-driven).

## Public API

```python
from visualizer import (
    EEGVisualizer,
    BoardStreamFeeder,
    get_visualizer_settings,
    VisualizerConfigError,
)
```

### `EEGVisualizer`

| Method / property | Behavior |
|-------------------|----------|
| `data_queue` | Subscribe from `EEGStreamController.add_subscriber()` |
| `start()` | Spawn plot process |
| `stop()` | Signal exit and join |
| `pause()` / `resume()` | Pause drawing |
| `mark(label)` | Marker line + label |
| `is_running` | Whether child process is alive |

### Standalone

`standalone.run_standalone()`:

1. Loads `EEG_VIS_*` from `.env`.
2. Opens BrainFlow session.
3. Starts `EEGVisualizer` + `BoardStreamFeeder`.

## Integrating with `experiment.py`

1. Create `EEGVisualizer` after the board is streaming.
2. `eeg_controller.add_subscriber(visualizer.data_queue)`.
3. `visualizer.start()` when acquisition starts.
4. `visualizer.pause()` / `resume()` with trial/block breaks.
5. `visualizer.stop()` on shutdown.

## Testing

```bash
cd ..
python -m pytest visualizer/tests -c visualizer/pyproject.toml -q
```

Core modules are measured with `fail_under = 100` in `.coveragerc` (`experiment.py` and `utils/` omitted).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Boxed config error on import | Set all three `EEG_VIS_*` in `.env` or pass kwargs to `EEGVisualizer()` |
| Blank plot | `data_queue` receiving copies from controller/feeder |
| Second window on Windows | Do not create `EEGVisualizer` at module import time in `experiment.py` |
