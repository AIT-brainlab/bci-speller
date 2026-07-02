import os
import time
from bci.board import SyntheticBoard, UnicornBoard

def main() -> None:
    use_unicorn = os.environ.get("USE_UNICORN", "0") == "1"
    board = UnicornBoard() if use_unicorn else SyntheticBoard()
    
    board_name = type(board).__name__
    print(f"=== Running with {board_name} ===")
    
    try:
        board.open()
        board.start_stream()
        status = board.get_status()
        
        print(f"Board type: {board_name}")
        print(f"Channel names: {board.channel_names}")
        print(f"Sampling rate: {status.sampling_rate} Hz")
        print(f"EEG channels: {status.n_channels}")
        
        time.sleep(5)
        
        # Read from raw_stream to get the accumulated data.
        stream = board.get_raw_stream()
        chunks = []
        while stream.size > 0:
            chunks.append(stream.get_nowait())
        
        if chunks:
            import numpy as np
            data = np.concatenate(chunks, axis=1)
            print(f"Data shape: {data.shape}")
        else:
            print("Data shape: (No data collected)")
            
    finally:
        board.close()
        # Print status after closing as requested by the supervisor
        final_status = board.get_status()
        print(f"Status: {final_status}")
        
    print()
    if not use_unicorn:
        print("--- To use real hardware, replace ONE line: ---")
        print("   board = SyntheticBoard()")
        print("   board = UnicornBoard()        <- only this changes")
        print("--- Everything else stays identical ---")
    else:
        print("--- To switch back to simulation, replace ONE line: ---")
        print("   board = UnicornBoard()")
        print("   board = SyntheticBoard()      <- only this changes")
        print("--- Everything else stays identical ---")

if __name__ == "__main__":
    main()
