"""
Launch the SSVEP 9-target stimulus presentation.

Flicker frequencies and target labels are loaded from speller_config by default,
or can be overridden with a JSON configuration file.
"""

from __future__ import annotations

import sys
from typing import Optional

from _bootstrap import bootstrap

_ROOT = bootstrap()

from bci.ui.ssvep.app import SSVEPStimulusApp


def run_launcher() -> int:
    # Try to load default parameters from speller_config
    default_config = {}
    try:
        from speller_config import FREQS, TARGET_CHARACTERS
        default_config["frequencies"] = FREQS
        default_config["labels"] = TARGET_CHARACTERS
    except ImportError:
        try:
            from visualizer.speller_config import FREQS, TARGET_CHARACTERS
            default_config["frequencies"] = FREQS
            default_config["labels"] = TARGET_CHARACTERS
        except ImportError:
            pass

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="SSVEP Standalone Stimulus Presentation")
    parser.add_argument("--config", type=str, default="", help="Path to config JSON file")
    parser.add_argument("--method", type=str, choices=["square-wave", "sine"], default="square-wave",
                        help="Flicker method (default: square-wave)")
    parser.add_argument("--hz", type=int, default=60, help="Flicker timer update/render rate (default: 60)")
    args = parser.parse_args()

    # If the user did not specify a config file, use the default config loaded from speller_config
    if not args.config:
        config = default_config
    else:
        from bci.ui.ssvep.app import load_config_json
        config = load_config_json(args.config)

    # CLI overrides
    if "flicker_method" not in config or args.method != "square-wave":
        config["flicker_method"] = args.method
    if "plot_hz" not in config or args.hz != 60:
        config["plot_hz"] = args.hz

    print(f"[Launcher] Starting SSVEP presentation.")
    print(f"  Frequencies: {config.get('frequencies')}")
    print(f"  Labels: {config.get('labels')}")
    print(f"  Method: {config.get('flicker_method')}")
    print(f"  Refresh rate: {config.get('plot_hz')} Hz")

    app = SSVEPStimulusApp(config)
    app.start()
    return 0


if __name__ == "__main__":
    sys.exit(run_launcher())
