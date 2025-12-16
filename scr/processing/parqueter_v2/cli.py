# cli.py
import click
import pymongo
from dotenv import load_dotenv
import os

from .helpers import compute_week_boundaries
from .processor import process_week

@click.command()
@click.option("--week", type=int, default=None, help="ISO week to process")
@click.option("--year", type=int, default=None, help="ISO year to process")
def run(week, year):
    load_dotenv()

    MONGO_URI = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(MONGO_URI)
    db = client["SteelArena"]
    collection = db["PRJ-16"]

    week_start, week_end, y, w = compute_week_boundaries(year, week)

    print(f"Processing ISO week {y}W{w:02d}")
    print("From:", week_start)
    print("To:  ", week_end)

    from pathlib import Path
    import json
    
    script_dir = Path(__file__).resolve().parent
    # scr/processing/parqueter_v2 -> ../../../
    repo_root = script_dir.parent.parent.parent
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

    process_week(collection, week_start, week_end, y, w, base_dir=parquet_dir)

if __name__ == "__main__":
    run()
