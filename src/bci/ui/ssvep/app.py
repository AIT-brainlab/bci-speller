"""SSVEP stimulus application using Matplotlib."""

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
        if platform.system() == "Windows":
            import win32api
            return int(win32api.GetSystemMetrics(0)), int(win32api.GetSystemMetrics(1))
    except Exception:
        pass
    return DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT


class SSVEPStimulusApp:
    """SSVEP standalone stimulus presentation app using Matplotlib."""

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
            default_freqs = speller_config.FREQS
            default_labels = speller_config.TARGET_CHARACTERS
            default_positions = speller_config.POSITIONS
            default_width = float(speller_config.WIDTH)
            default_height = float(speller_config.HEIGHT)
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

        self.targets = generate_3x3_grid(self.config)
        self.plot_hz = int(self.config.get("plot_hz", 60))
        
        # Color palette: Dark background, white text, squares flicker between white and dark grey
        self.bg_color = self.config.get("bg_color", "#121212")
        self.color_on = self.config.get("color_on", "#FFFFFF")     # White
        self.color_off = self.config.get("color_off", "#333333")   # Dark grey
        self.text_color = self.config.get("text_color", "#FFFFFF") # White text

        self.target_width = float(self.config.get("target_width_pixels", default_width))
        self.target_height = float(self.config.get("target_height_pixels", default_height))

        # Lazy-loaded Matplotlib variables to prevent shadowing issues in test runner
        self.fig: Any = None
        self.ax: Any = None
        self.rects: list[Any] = []
        self.start_time: float = 0.0
        self.is_running: bool = False
        self._ani: Any = None

    def start(self) -> None:
        """Create the Matplotlib window and start the flicker animation loop."""
        import matplotlib
        matplotlib.use("TkAgg")
        # Disable the Matplotlib toolbar for a clean speller UI
        matplotlib.rcParams['toolbar'] = 'None'
        
        import matplotlib.animation as animation
        import matplotlib.patches as patches
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as path_effects
        from matplotlib.colors import to_rgb

        self.is_running = True
        
        self.fig, self.ax = plt.subplots(figsize=(12, 9))
        self.fig.patch.set_facecolor(self.bg_color)
        self.ax.set_facecolor(self.bg_color)

        # Retrieve resolution to set coordinate limits matching speller pixels
        width, height = _get_screen_resolution()
        self.ax.set_xlim(-width / 2, width / 2)
        self.ax.set_ylim(-height / 2, height / 2)
        self.ax.set_axis_off()
        
        # Lock aspect ratio to 1:1 so squares are never stretched
        self.ax.set_aspect('equal', adjustable='box')
        
        # Remove default padding/margins around the plot
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

        # Parse colors to RGB
        rgb_on = to_rgb(self.color_on)
        rgb_off = to_rgb(self.color_off)

        self.rects = []

        # Draw targets and labels in exact original speller style
        for target in self.targets:
            x, y = target.position
            # Draw rectangle centered at (x, y), starting in OFF (dark) state
            rect = patches.Rectangle(
                (x - self.target_width / 2, y - self.target_height / 2),
                self.target_width, self.target_height,
                facecolor=self.color_off,
                edgecolor="#555555",
                linewidth=0.8,
                zorder=1,
            )
            self.ax.add_patch(rect)
            self.rects.append(rect)

            # White label with a thin black outline — readable on both bright (ON)
            # and dark (OFF) box states.
            txt = self.ax.text(
                x, y, target.label,
                color=self.text_color,
                fontsize=14,
                fontweight="bold",
                fontname="DejaVu Sans",
                ha="center", va="center",
                zorder=2,
            )
            txt.set_path_effects([
                path_effects.withStroke(linewidth=2.5, foreground='#000000'),
            ])

        # Hook key press to exit on Escape
        def on_key(event: Any) -> None:
            if event.key == "escape":
                plt.close(self.fig)

        self.fig.canvas.mpl_connect("key_press_event", on_key)

        # Attempt to maximize window for fullscreen experience
        try:
            self.fig.canvas.manager.window.state('zoomed')
        except Exception:
            try:
                self.fig.canvas.manager.full_screen_toggle()
            except Exception:
                pass

        self.start_time = time.perf_counter()

        # Pre-cache arrays for ultra-fast, jitter-free vector calculations
        self_rects = self.rects
        num_targets = len(self.targets)
        freqs = np.array([t.frequency for t in self.targets], dtype=np.float64)
        is_square = np.array([t.pattern == "square-wave" for t in self.targets], dtype=bool)
        
        rgb_off_arr = np.array(rgb_off, dtype=np.float64)
        rgb_diff_arr = np.array(rgb_on, dtype=np.float64) - rgb_off_arr

        # FuncAnimation update function
        def _update(frame: int) -> list[Any]:
            if not self.is_running or self.fig is None or not plt.fignum_exists(self.fig.number):
                return []

            t = time.perf_counter() - self.start_time
            
            # Vectorized timing calculation
            angles = 2.0 * np.pi * freqs * t
            sines = np.sin(angles)
            
            # Compute states (0.0 to 1.0)
            vals = np.where(is_square, np.where(sines >= 0.0, 1.0, 0.0), 0.5 + 0.5 * sines)
            
            # Compute RGB values
            colors = rgb_off_arr + vals[:, np.newaxis] * rgb_diff_arr

            # Assign to patches
            for i in range(num_targets):
                self_rects[i].set_facecolor(colors[i])

            return self_rects

        interval_ms = int(1000 / self.plot_hz)
        # blit=False is required so that Matplotlib correctly redraws text labels on top of updated rectangles
        self._ani = animation.FuncAnimation(
            self.fig, _update, interval=interval_ms, blit=False, cache_frame_data=False
        )

        try:
            self.fig.canvas.manager.set_window_title("SSVEP Stimulus Matrix")
        except Exception:
            pass

        plt.show()
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


def main(argv: Optional[list[str]] = None) -> int:
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


if __name__ == "__main__":
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
