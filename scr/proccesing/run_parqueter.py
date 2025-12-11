# run_parqueter.py
from dotenv import load_dotenv
import pymongo
from scr.processing.parqueter_v2.helpers import compute_week_boundaries
from scr.processing.parqueter_v2.processor import process_week

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = pymongo.MongoClient(MONGO_URI)
collection = client["SteelArena"]["PRJ-16"]

start_dt, end_dt, y, w = compute_week_boundaries()

process_week(collection, start_dt, end_dt, y, w)

print("DONE.")
