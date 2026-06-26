import typer
from rich import print
from typing import Annotated, Optional
import time
from pathlib import Path

cli = typer.Typer(
    no_args_is_help=True,
    help="BCI Speller CLI for monitoring, recording, and stimulus.")

def get_board(
    synthetic: bool, 
    board_id: int, 
    serial: str, 
    n_channels: int
):
    from bci.board.synthetic import SyntheticBoard
    from bci.board.brainflow_board import BrainFlowBoard
    
    if board_id > 0 and synthetic:
        # If user explicitly specifies a real board ID, disable synthetic
        synthetic = False

    if synthetic or board_id <= 0:
        board = SyntheticBoard(n_channels=n_channels, sampling_rate=250)
    else:
        board = BrainFlowBoard(board_id=board_id, serial_number=serial)
    
    print(f"[bold blue][BCI][/bold blue] Opening board (board_id={board.get_status().board_id})...")
    board.open()
    board.start_stream()
    return board

@cli.command()
def monitor(
    synthetic: Annotated[bool, typer.Option(help="Use synthetic board")] = True,
    board_id: Annotated[int, typer.Option(help="BrainFlow board ID")] = -1,
    serial: Annotated[str, typer.Option(help="Serial number for physical board")] = "",
    channels: Annotated[int, typer.Option("--channels", "-c", help="Number of channels")] = 8,
    window: Annotated[float, typer.Option("--window", "-w", help="Timeline window in seconds")] = 5.0,
    hz: Annotated[int, typer.Option("--hz", help="Plot refresh rate in Hz")] = 20,
    amplitude: Annotated[float, typer.Option("--amplitude", "-a", help="EEG amplitude range (uV)")] = 100.0,
    monitor_index: Annotated[int, typer.Option("--monitor", "-m", help="Monitor index")] = 1,
):
    """Launch the live signal monitor UI."""
    from bci.ui.signal_monitor.app import SignalMonitorApp
    
    board = get_board(synthetic, board_id, serial, channels)
    
    print("[bold blue][BCI][/bold blue] Starting monitor app...")
    app = SignalMonitorApp(
        board=board,
        n_channels=channels,
        window_sec=window,
        plot_hz=hz,
        amplitude_uv=amplitude,
        monitor_index=monitor_index,
    )
    app.start()

    try:
        while app.is_running:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[bold yellow][BCI] Interrupted by user[/bold yellow]")
    finally:
        app.stop()
        board.stop_stream()
        board.close()

@cli.command()
def ssvep(
    hz: Annotated[int, typer.Option("--hz", help="Stimulus refresh rate")] = 60,
    width: Annotated[float, typer.Option("--width", help="Target width (pixels)")] = 100.0,
    height: Annotated[float, typer.Option("--height", help="Target height (pixels)")] = 100.0,
):
    """Launch the SSVEP stimulus presentation."""
    from bci.ui.ssvep.app import SSVEPStimulusApp
    
    config = {
        "plot_hz": hz,
        "target_width_pixels": width,
        "target_height_pixels": height,
    }
    
    print("[bold blue][BCI][/bold blue] Starting SSVEP stimulus app...")
    app = SSVEPStimulusApp(config=config)
    app.start()
