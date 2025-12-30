# %pip install python-dotenv pymongo requests  # Uncomment if you need to install these
import requests
import os
from dotenv import load_dotenv
import pymongo
from datetime import datetime, UTC

# Load variables from .env file
load_dotenv()

# Access the variables
MONGO_URI = os.getenv("MONGO_URI_WRT")
API_KEY = os.getenv("WEATHER_API_KEY")

# Quick validation (without printing sensitive keys)
if not MONGO_URI or not API_KEY:
    print("❌ Error: MONGO_URI or WEATHER_API_KEY not found in .env file.")
else:
    print("✅ Environment variables loaded successfully.")

# --- CONFIG ---
DB_NAME = "prod"
COLL_NAME = "PRJ-27"

# Define your locations (Name: (Lat, Lon))
LOCATIONS = {
    "PRJ-16": (48.715093, 21.248317),
    "PRJ-15": (49.061093, 20.087783),
    "PRJ-19": (48.745003, 19.229697)
}

# Initialize Client
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLL_NAME]

# Test connection
try:
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")    

# --- UPDATED TRANSFORM FUNCTION ---
def transform_weather(data: dict, project_id: str) -> dict:
    epoch = data.get("dt")
    utc_dt = datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%d %H:%M:%S")

    weather = data["weather"][0] if data.get("weather") else {}
    main = data.get("main", {})
    
    # Precipitation is optional in the API response
    rain = data.get("rain", {}).get("1h", 0)
    snow = data.get("snow", {}).get("1h", 0)

    return {
        "project": project_id,
        # "api_location_name": data.get("name"),
        "coords": {
            "lat": data.get("coord", {}).get("lat"),
            "lon": data.get("coord", {}).get("lon")
        },
        "values": {
            "sky": {
                "main": weather.get("main"),
                "description": weather.get("description"),
                "clouds": data.get("clouds", {}).get("all"),
                "visibility": data.get("visibility")
            },
            "air": {
                "temp": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "pressure": main.get("pressure"),
                "humidity": main.get("humidity"),
                "sea_level": main.get("sea_level"),
                "grnd_level": main.get("grnd_level"),
            },
            "wind": data.get("wind", {}),
            "precipitation": {
                "rain_1h_mm": rain,
                "snow_1h_mm": snow
            }
        },
        "time": {
            "epoch": epoch,
            "UTC": utc_dt
        }
    }

# --- EXECUTION LOOP ---
prepared_documents = []

for project_id, (lat, lon) in LOCATIONS.items():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        raw_json = response.json()
        
        # Transform and add to our list
        clean_doc = transform_weather(raw_json, project_id)
        prepared_documents.append(clean_doc)
        
        print(f"✅ Prepared: {project_id}")
        
    except Exception as e:
        print(f"❌ Failed {project_id}: {e}")

# Verify and Upload
print(f"\nTotal documents fetched: {len(prepared_documents)}")

if prepared_documents:
    print("🔍 Checking for duplicates in MongoDB...")
    
    # Fetch last few entries from MongoDB to compare
    # We check slightly more than we have locations to be safe
    recent_docs = list(collection.find({}, {"project": 1, "time.epoch": 1})
                       .sort("_id", pymongo.DESCENDING)
                       .limit(len(LOCATIONS) * 2))
    
    # Create a set of "project_epoch" keys already in the DB
    existing_keys = {f"{d['project']}_{d['time']['epoch']}" for d in recent_docs if 'time' in d}

    docs_to_insert = []
    for doc in prepared_documents:
        key = f"{doc['project']}_{doc['time']['epoch']}"
        if key in existing_keys:
            continue
        docs_to_insert.append(doc)

    skipped_count = len(prepared_documents) - len(docs_to_insert)

    if docs_to_insert:
        try:
            result = collection.insert_many(docs_to_insert)
            print("\n--- MongoDB Upload Status ---")
            print(f"✅ Successfully inserted {len(result.inserted_ids)} new documents.")
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} duplicates.")
        except Exception as e:
            print(f"❌ MongoDB Insertion Error: {e}")
    else:
        print(f"\n✅ All {len(prepared_documents)} documents already exist in MongoDB. Nothing to push.")
else:
    print("⚠️ No documents were prepared.")