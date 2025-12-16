# run_parqueter.py
from dotenv import load_dotenv
import os
import json
import pymongo
from parqueter_v2.helpers import compute_week_boundaries
from parqueter_v2.processor import process_week

from pathlib import Path

# Load config robustly
script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent.parent
config_path = repo_root / "config" / "path.json"

parquet_dir = "parquet_output"
if config_path.exists():
    with open(config_path, "r") as f:
        config = json.load(f)
    parquet_dir = config.get("parquet_dir", "data/parquet/")
    
    # Resolve to absolute path centered at repo root
    p_path = Path(parquet_dir)
    if not p_path.is_absolute():
        p_path = repo_root / p_path
    parquet_dir = str(p_path)

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = pymongo.MongoClient(MONGO_URI)
collection = client["prod"]["PRJ-16"]

start_dt, end_dt, y, w = compute_week_boundaries()

process_week(collection, start_dt, end_dt, y, w, base_dir=parquet_dir)

print("DONE.")
