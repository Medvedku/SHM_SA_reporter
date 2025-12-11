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

    process_week(collection, week_start, week_end, y, w)

if __name__ == "__main__":
    run()
