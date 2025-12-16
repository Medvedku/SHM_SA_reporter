from pathlib import Path
import json

# --- repo root (based on THIS file location) ---
ROOT = Path(__file__).resolve().parents[3]

# --- load paths ---
with open(ROOT / "config/path.json") as f:
    PATHS = json.load(f)

DUCK_DIR = ROOT / PATHS["duck_dir"]
DB_FILE  = DUCK_DIR / "shm_report.duckdb"

if DB_FILE.exists():
    DB_FILE.unlink()
    print("🗑 DuckDB removed:", DB_FILE)
else:
    print("⚠ DuckDB not found:", DB_FILE)
