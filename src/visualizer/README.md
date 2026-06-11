# EEG Visualizer

Live multi-channel EEG plot for BrainFlow-based BCI experiments.

## Requirements checklist

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Run without experiment / PsychoPy | `python -m visualizer` |
| 2 | Reusable class in its own file | `live_monitor_class.py` → `EEGVisualizer` |
| 3 | Plot settings via `.env` + clear errors | `EEG_VIS_*` in `config/settings.py` |
| 4 | Type hints | Yes (`py.typed` optional) |
| 5 | README + manual | This file + `MANUAL.md` |
| 6 | Unit tests, **100%** on core modules | `tests/`, `.coveragerc` |
| 7 | Clean `__init__` exports | `from visualizer import EEGVisualizer` |
| 8 | Pydantic validation | `VisualizerSettings` |

## Quick start

### 1. Configure (required)

```bash
cd visualizer
copy .env.example .env
```

| Variable | Meaning |
|----------|---------|
| `EEG_VIS_WINDOW_SEC` | Rolling plot window (seconds) |
| `EEG_VIS_PLOT_HZ` | UI refresh rate (frames/s) |
| `EEG_VIS_AMPLITUDE_UV` | Y-axis half-range (µV) |

### 2. Standalone (no experiment)

From the parent folder (`Internship/`):

```bash
pip install -r visualizer/requirements.txt
python -m visualizer
```

Or use the IDE **Run** button on `live_monitor.py` (same standalone mode).

### 3. Inside the speller experiment

```python
from visualizer import EEGVisualizer

visualizer = EEGVisualizer(
    board_shim=board_shim,
    board_id=BOARD_ID,
    n_channels=8,
    window_sec=5,
    plot_hz=20,
    amplitude_uv=100,
)
eeg_controller.add_subscriber(visualizer.data_queue)
visualizer.start()
```

## Package layout

```
visualizer/
├── config/                  # Pydantic settings (EEG_VIS_*)
├── live_monitor_class.py  # EEGVisualizer class
├── live_monitor.py        # Public re-exports
├── process.py               # Matplotlib child process
├── stream_feeder.py         # Standalone board → queue
├── standalone.py            # CLI entry
├── experiment.py            # Full PsychoPy speller (optional)
└── tests/                   # Unit tests, 100% core coverage
```

## Tests

```bash
cd ..
python -m pytest visualizer/tests -c visualizer/pyproject.toml
```

## Related folder: `live_monitor/`

A renamed copy of this package exists at `../live_monitor/` (same design, `LiveMonitor` + `LIVE_MONITOR_*`). **Develop here in `visualizer/`** — this is your Cursor workspace. Both folders are siblings under `Internship/`.
