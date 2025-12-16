from pathlib import Path
import json
import duckdb

# --- repo root (based on THIS file location) ---
ROOT = Path(__file__).resolve().parents[3]

# --- load paths ---
with open(ROOT / "config/path.json") as f:
    PATHS = json.load(f)

PARQUET_DIR = ROOT / PATHS["parquet_dir"]
DUCK_DIR    = ROOT / PATHS["duck_dir"]
DUCK_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DUCK_DIR / "shm_report.duckdb"

# --- recreate DB ---
if DB_FILE.exists():
    DB_FILE.unlink()

con = duckdb.connect(str(DB_FILE))
print("Creating:", DB_FILE)

# --- load all parquets ---
for pf in sorted(PARQUET_DIR.glob("*.parquet")):
    name = pf.name
    table = name[8:-8]   # strip week + suffix

    print(f"\n=== Building table '{table}' from {name} ===")

    con.execute(f"""
        CREATE TABLE {table} AS
        SELECT * FROM parquet_scan('{pf}');
    """)

# --- force materialization ---
con.execute("ALTER TABLE accel_all ADD COLUMN __force_write__ INT DEFAULT 0;")
con.execute("ALTER TABLE accel_all DROP COLUMN __force_write__;")

con.close()

print("✔ File exists:", DB_FILE.exists())
print("✔ DB path:", DB_FILE)
