import time
import psutil
import sys
from pathlib import Path

# Add current directory to path to ensure run_plotter_v2 can be imported
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import run_plotter_v2

def get_ram_mb():
    return psutil.Process().memory_info().rss / 1024 / 1024

def main():
    print("--- wrapper: ram_run_plotter_v2 ---")
    
    ram_before = get_ram_mb()
    t0 = time.time()

    # run_plotter_v2.main executes the sequence of subprocesses
    try:
        run_plotter_v2.main()
    except SystemExit as e:
        # Catch clean exits to print metrics
        if e.code not in [None, 0]:
             print(f"Exited with code: {e.code}")

    ram_after = get_ram_mb()
    t1 = time.time()

    print("\n===== PLOTTER RUN METRICS =====")
    print(f"RAM before:   {ram_before:10.2f} MB")
    print(f"RAM after:    {ram_after:10.2f} MB")
    print(f"RAM change:   {ram_after - ram_before:10.2f} MB")
    print(f"Runtime:      {t1 - t0:10.2f} seconds")
    print("=================================\n")

if __name__ == "__main__":
    main()
