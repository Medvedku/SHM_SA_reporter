from pathlib import Path
import json
import duckdb
import plotly_functions

# --- repo root (based on THIS file location) ---
ROOT = Path(__file__).resolve().parents[3]

# --- load paths ---
with open(ROOT / "config/path.json") as f:
    PATHS = json.load(f)

PARQUET_DIR = ROOT / PATHS["parquet_dir"]
DUCK_DIR    = ROOT / PATHS["duck_dir"]
DUCK_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DUCK_DIR / "shm_report.duckdb"

con = duckdb.connect(str(DB_FILE))


# --- Auto-detect start/end datetime from the weekly DB ---
row = con.execute("""
    SELECT MIN(datetime) AS start_dt,
           MAX(datetime) AS end_dt
    FROM sst_hub1
""").fetchone()

start_dt, end_dt = row[0], row[1]

print("Detected week range:")
print("Start:", start_dt)
print("End:  ", end_dt)


plotly_functions.temps_col_plotly(con, save=True, show=False, bin_time=60)
plotly_functions.temps_arch_plotly(con, save=True, show=False, bin_time=60)


for nmbr in range(6):
    snsr_id = (f'A3{nmbr}')
    plotly_functions.fft_with_KDE_plotly(con, sensor_id=snsr_id, show=False, save=True)
    plotly_functions.accel_v_daily_grid_plotly(con, sensor_id=snsr_id, show=False, save=True)


for nmbr in range(7, 30):
    snsr_id = (f'S{nmbr}')
    plotly_functions.strain_temp_plotly(con, sensor_id=snsr_id, show=False, save=True, bin_time=20)

con.close()

print("Done m8")