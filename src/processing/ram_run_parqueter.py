# run_parqueter.py

import parqueter_v2.processor as p

print("USING processor:", p.__file__)


import os
import psutil
import time
from dotenv import load_dotenv
import pymongo

from parqueter_v2.processor import process_week
from parqueter_v2.helpers import compute_week_boundaries


def get_ram_mb():
    return psutil.Process().memory_info().rss / 1024 / 1024


def main():
    load_dotenv()

    MONGO_URI = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(MONGO_URI)
    collection = client["prod"]["PRJ-16"]

    start_dt, end_dt, y, w = compute_week_boundaries()

    # --- RAM + time before ---
    ram_before = get_ram_mb()
    t0 = time.time()

    print(f"Processing ISO week {y}W{w:02d}")
    print("Start:", start_dt)
    print("End:  ", end_dt)

    from pathlib import Path
    import json

    # Robustly find config/path.json relative to this script
    # script is in src/processing/ -> root is ../../
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    config_path = repo_root / "config" / "path.json"

    parquet_dir = "parquet_output"  # Fallback
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        parquet_dir = config.get("parquet_dir", "data/parquet/")
        # Ensure it's absolute or relative to CWD correctly?
        # config paths are usually relative to repo root.
        # If running from script dir, we might need to adjust.
        # But usually data/ is in root.
        # So we should probably prepend repo_root if it's relative?
        # The writer uses it as base_dir.
        # If I pass "data/parquet/", and run from src/processing/, it will try src/processing/data/parquet/
        # UNLESS the user runs from root.

        # To be safe, let's make it absolute based on repo_root
        parquet_path = Path(parquet_dir)
        if not parquet_path.is_absolute():
            parquet_path = repo_root / parquet_path
        parquet_dir = str(parquet_path)

    process_week(collection, start_dt, end_dt, y, w, base_dir=parquet_dir)

    # --- RAM + time after ---
    ram_after = get_ram_mb()
    t1 = time.time()

    print("\n===== PARQUETER RUN METRICS =====")
    print(f"RAM before:   {ram_before:10.2f} MB")
    print(f"RAM after:    {ram_after:10.2f} MB")
    print(f"RAM change:   {ram_after - ram_before:10.2f} MB")
    print(f"Runtime:      {t1 - t0:10.2f} seconds")
    print("=================================\n")


if __name__ == "__main__":
    main()
