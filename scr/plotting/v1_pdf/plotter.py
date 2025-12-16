import duckdb
import pandas as pd
from pathlib import Path
import json
import plot_functions
import argparse


# ============================================================
# ARGUMENTS & SETUP
# ============================================================

parser = argparse.ArgumentParser(description="Generate plots for a given time window.")
parser.add_argument("--end-date", help="END date (YYYY-MM-DD)")
parser.add_argument("--start-date", help="START date (YYYY-MM-DD). If omitted, start = end - 7 days")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()


# ============================================================
# LOAD CONFIG PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH  = PROJECT_ROOT / "config" / "path.json"

with open(CONFIG_PATH, "r") as f:
    paths = json.load(f)

# Path to external .duckdb file (your case)
DB_FILE = Path(paths.get("database_path", "/home/moshe/Documents/GitHub/SA_analysis/SA_analysis/database/shm.duckdb"))

if args.verbose:
    print("Using DB:", DB_FILE)


# ============================================================
# CONNECT TO DUCKDB
# ============================================================

con = duckdb.connect(str(DB_FILE))
if args.verbose:
    print(con.execute("PRAGMA database_list").df())


# ============================================================
# DEFINE ANALYSIS WINDOW
# ============================================================

if args.end_date:
    END_DT = pd.to_datetime(args.end_date)
    if args.start_date:
        START_DT = pd.to_datetime(args.start_date)
    else:
        START_DT = END_DT - pd.Timedelta(days=7)
else:
    # Backwards-compatible interactive prompt
    END_DT_plain = input("Enter END date (YYYY-MM-DD): ").strip()
    END_DT = pd.to_datetime(END_DT_plain)
    START_DT = END_DT - pd.Timedelta(days=7)

if args.verbose:
    print(f"Using analysis window:")
    print(f"  START_DT = {START_DT}")
    print(f"  END_DT   = {END_DT}")


# ============================================================
# RUN ALL PLOTS
# ============================================================

if args.verbose:
    print("\n=== Generating Temperature Plots ===")
plot_functions.temps_col(
    con,
    start_dt=START_DT,
    end_dt=END_DT,
    show=False,
    save=True
)

plot_functions.temps_arch(
    con,
    start_dt=START_DT,
    end_dt=END_DT,
    show=False,
    save=True
)


if args.verbose:
    print("\n=== Generating FFT + KDE Plots ===")
for sid in ["A30", "A31", "A32", "A33", "A34", "A35"]:
    plot_functions.fft_with_KDE_plot(
        con,
        sensor_id=sid,
        threshold=0.08,
        start_dt=START_DT,
        end_dt=END_DT,
        show=False,
        save=True
    )


if args.verbose:
    print("\n=== Generating Strain-Temperature Plots ===")
for sid in [
    "S7","S8","S9","S10","S11","S12","S13","S14",
    "S15","S16","S17","S18",
    "S19","S20","S21","S22","S23","S24","S25","S26",
    "S27","S28","S29"
]:
    plot_functions.strain_temp_plot(
        con,
        sensor_id=sid,
        start_dt=START_DT,
        end_dt=END_DT,
        show=False,
        save=True
    )


if args.verbose:
    print("\n=== Generating Accel Daily Grid Plots ===")
for sid in ["A30", "A31", "A32", "A33", "A34", "A35"]:
    plot_functions.accel_v_daily_grid(
        con,
        sensor_id=sid,
        start_dt=START_DT,
        end_dt=END_DT,
        show=False,
        save=True
    )

if args.verbose:
    print("\n=== ALL PLOTS GENERATED ===\n")
