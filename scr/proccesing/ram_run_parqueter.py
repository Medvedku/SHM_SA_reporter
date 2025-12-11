# run_parqueter.py
import os
import psutil
import time
from dotenv import load_dotenv
import pymongo

from parqueter_v2.helpers import compute_week_boundaries
from parqueter_v2.processor import process_week


def get_ram_mb():
    return psutil.Process().memory_info().rss / 1024 / 1024


def main():
    load_dotenv()

    MONGO_URI = os.getenv("MONGODB_URI")
    client = pymongo.MongoClient(MONGO_URI)
    collection = client["SteelArena"]["PRJ-16"]

    start_dt, end_dt, y, w = compute_week_boundaries()

    # --- RAM + time before ---
    ram_before = get_ram_mb()
    t0 = time.time()

    print(f"Processing ISO week {y}W{w:02d}")
    print("Start:", start_dt)
    print("End:  ", end_dt)

    process_week(collection, start_dt, end_dt, y, w)

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
