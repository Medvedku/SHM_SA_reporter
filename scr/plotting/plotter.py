import duckdb
import pandas as pd
from pathlib import Path
import json
import plot_functions


# ============================================================
# LOAD CONFIG PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH  = PROJECT_ROOT / "config" / "path.json"

with open(CONFIG_PATH, "r") as f:
    paths = json.load(f)

# Path to external .duckdb file (your case)
DB_FILE = Path(paths.get("database_path", "/home/moshe/Documents/GitHub/SA_analysis/SA_analysis/database/shm.duckdb"))

print("Using DB:", DB_FILE)


# ============================================================
# CONNECT TO DUCKDB
# ============================================================

con = duckdb.connect(str(DB_FILE))
print(con.execute("PRAGMA database_list").df())


# ============================================================
# DEFINE ANALYSIS WINDOW
# ============================================================

# Example: Start at 10 Nov 2025 → end automatically = MAX(datetime)
END_DT = pd.to_datetime("2025-04-10")
START_DT = END_DT - pd.Timedelta(days=7)


# ============================================================
# RUN ALL PLOTS
# ============================================================

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

print("\n=== ALL PLOTS GENERATED ===\n")
