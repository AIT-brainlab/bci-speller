## Board Configuration

The BCI speller supports multiple hardware boards for EEG acquisition. Switching between boards is designed to be seamless.

### Supported Boards

| Board Class | Use Case | Description |
|-------------|----------|-------------|
| `SyntheticBoard` | Development | No hardware required. Generates synthetic EEG-like data for testing. |
| `UnicornBoard` | Real Recording | Interfaces with the physical g.tec Unicorn Hybrid Black EEG headset. |

### Switching Boards

You can switch between boards without modifying the core business logic. The `BoardInterface` guarantees a consistent API across implementations.

```python
from bci.board import SyntheticBoard, UnicornBoard

# For development without hardware:
board = SyntheticBoard()

# For real recordings with the headset:
board = UnicornBoard()
```

### Unicorn Hardware Setup

To use the `UnicornBoard`:
1. Connect the Unicorn USB dongle to your computer.
2. Pair the headset via the dongle (do **not** pair via the built-in Bluetooth of your computer).
3. The board is fully supported on Windows and Ubuntu 18.04+.
4. (Optional) If you have multiple Unicorn devices nearby, you can pass its serial number during initialization: `UnicornBoard(serial_number="UN-2021.05.51")`.

### Running the Example

An example script is provided in `src/project/examples/board_example.py` that demonstrates board switching using an environment variable (`USE_UNICORN`).

To run with the **SyntheticBoard** (default, no hardware):
```bash
uv run python src/project/examples/board_example.py
```

To run with the **UnicornBoard** (requires paired hardware):
```bash
USE_UNICORN=1 uv run python src/project/examples/board_example.py
```
