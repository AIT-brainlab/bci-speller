"""SSVEP stimulus application using PsychoPy."""

from __future__ import annotations

import os
import platform
import sys
import time
from typing import Any, Optional

import numpy as np

# Resolution fallback defaults
DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080


def _get_screen_resolution() -> tuple[int, int]:
    """Retrieve screen resolution using platform API."""
    try:
        if platform.system() == "Windows":  # pragma: no cover
            import win32api
            return int(win32api.GetSystemMetrics(0)), int(win32api.GetSystemMetrics(1))
    except Exception:  # pragma: no cover
        pass
    return DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT


def hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """Convert hex string to PsychoPy [-1, 1] RGB tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (r / 127.5 - 1.0, g / 127.5 - 1.0, b / 127.5 - 1.0)


class SSVEPStimulusApp:
    """SSVEP standalone stimulus presentation app using PsychoPy."""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        from bci.ui.ssvep.stimulus import generate_3x3_grid

        self.config = config or {}
        
        # Load configuration, defaulting to speller_config if available
        default_freqs = None
        default_labels = None
        default_positions = None
        default_width = 100.0
        default_height = 100.0
        
        try:
            import speller_config
            default_freqs = speller_config.FREQS  # pragma: no cover
            default_labels = speller_config.TARGET_CHARACTERS  # pragma: no cover
            default_positions = speller_config.POSITIONS  # pragma: no cover
            default_width = float(speller_config.WIDTH)  # pragma: no cover
            default_height = float(speller_config.HEIGHT)  # pragma: no cover
        except ImportError:
            try:
                import visualizer.speller_config as speller_config
                default_freqs = speller_config.FREQS
                default_labels = speller_config.TARGET_CHARACTERS
                default_positions = speller_config.POSITIONS
                default_width = float(speller_config.WIDTH)
                default_height = float(speller_config.HEIGHT)
            except ImportError:
                pass

        if "frequencies" not in self.config and default_freqs is not None:
            self.config["frequencies"] = default_freqs
        if "labels" not in self.config and default_labels is not None:
            self.config["labels"] = default_labels
        if "positions" not in self.config and default_positions is not None:
            self.config["positions"] = default_positions

        self.plot_hz = int(self.config.get("plot_hz", 60))
        
        # Color palette
        self.bg_color = self.config.get("bg_color", "#121212")
        self.color_on = self.config.get("color_on", "#FFFFFF")     # White
        self.color_off = self.config.get("color_off", "#333333")   # Dark grey
        self.text_color = self.config.get("text_color", "#FFFFFF") # White text

        self.target_width = float(self.config.get("target_width_pixels", default_width))
        self.target_height = float(self.config.get("target_height_pixels", default_height))

        # Lazy-loaded PsychoPy window variable
        self.win: Any = None
        self.start_time: float = 0.0
        self.is_running: bool = False
        
        # Pre-generate targets (without window binding initially)
        self.targets = generate_3x3_grid(self.config)

    def start(self) -> None:  # pragma: no cover
        """Create the PsychoPy window and start the frame-locked animation loop."""
        from psychopy import visual, event
        
        self.is_running = True
        
        width, height = _get_screen_resolution()
        bg_rgb = hex_to_rgb(self.bg_color)
        text_rgb = hex_to_rgb(self.text_color)
        
        # Open a full-screen window with standard black background
        self.win = visual.Window(
            size=(width, height),
            fullscr=True,
            units='pix',
            color=bg_rgb,
            colorSpace='rgb',
            allowGUI=False,
        )
        
        # Update target parameters and initialize their visuals
        for target in self.targets:
            target.width = self.target_width
            target.height = self.target_height
            target.color_off = self.color_off
            target.text_color = text_rgb
            target.init_visuals(self.win)
            
        self.start_time = time.perf_counter()
        
        rgb_on = np.array(hex_to_rgb(self.color_on), dtype=np.float64)
        rgb_off = np.array(hex_to_rgb(self.color_off), dtype=np.float64)
        rgb_diff = rgb_on - rgb_off
        
        while self.is_running:
            keys = event.getKeys()
            if "escape" in keys:
                self.is_running = False
                break
                
            t = time.perf_counter() - self.start_time
            
            for target in self.targets:
                if target.rect is None:
                    continue
                # Calculate flicker state
                phase = 2.0 * np.pi * target.frequency * t
                sin_val = np.sin(phase)
                
                if target.pattern == "square-wave":
                    val = 1.0 if sin_val >= 0.0 else 0.0
                else:
                    val = 0.5 + 0.5 * sin_val
                    
                col = rgb_off + val * rgb_diff
                target.rect.fillColor = col
                target.draw()
                
            self.win.flip()
            
        self.win.close()
        self.is_running = False


def load_config_json(filepath: str) -> dict[str, Any]:
    """Helper to load configuration dict from JSON file."""
    import json
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[SSVEP App] Warning: failed to load JSON config from {filepath}: {exc}. Using defaults.")
        return {}


def main(argv: Optional[list[str]] = None) -> int:  # pragma: no cover
    """Run standalone SSVEP presentation window."""
    import argparse

    parser = argparse.ArgumentParser(description="SSVEP Standalone Stimulus Presentation")
    parser.add_argument("--config", type=str, default="", help="Path to config JSON file")
    parser.add_argument("--method", type=str, choices=["square-wave", "sine"], default="square-wave",
                        help="Flicker method (default: square-wave)")
    parser.add_argument("--hz", type=int, default=60, help="Flicker timer update/render rate (default: 60)")
    args = parser.parse_args(argv)

    config = {}
    if args.config:
        config = load_config_json(args.config)

    # CLI overrides
    if "flicker_method" not in config or args.method != "square-wave":
        config["flicker_method"] = args.method
    if "plot_hz" not in config or args.hz != 60:
        config["plot_hz"] = args.hz

    print(f"[SSVEP App] Starting presentation. Flicker method: {config['flicker_method']}, rate: {config['plot_hz']} Hz")
    app = SSVEPStimulusApp(config)
    app.start()
    print("[SSVEP App] Stopped")
    return 0


if __name__ == "__main__":  # pragma: no cover
    # Add project paths to import from bci namespace when run as script
    import sys
    from pathlib import Path
    _file_path = Path(__file__).resolve()
    _bci_dir = _file_path.parents[2]
    _viz_root = _file_path.parents[3]
    for _p in (_viz_root.parent, _bci_dir, _viz_root):
        _entry = str(_p)
        if _entry not in sys.path:
            sys.path.insert(0, _entry)

    sys.exit(main())
