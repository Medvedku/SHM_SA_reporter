import os
import json
import logging
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# --- GCP config ---
GCP_CREDENTIALS_JSON = os.getenv("GCP_CREDENTIALS_JSON")
BUCKET_NAME = "shm-reports"

if not GCP_CREDENTIALS_JSON:
    raise ValueError("GCP_CREDENTIALS_JSON environment variable is missing!")

# Parse credentials from environment variable
creds_dict = json.loads(GCP_CREDENTIALS_JSON)
credentials = service_account.Credentials.from_service_account_info(creds_dict)

# Create GCP Storage client
client = storage.Client(credentials=credentials, project=creds_dict["project_id"])
bucket = client.bucket(BUCKET_NAME)

# --- repo root ---
ROOT = Path(__file__).resolve().parents[2]

# --- load paths ---
with open(ROOT / "config/path.json") as f:
    PATHS = json.load(f)

REPORTS_DIR = ROOT / PATHS["report_dir"]

if not REPORTS_DIR.exists():
    raise FileNotFoundError(f"Reports dir not found: {REPORTS_DIR}")

logger.info(f"Connected to GCP Storage")
logger.info(f"Bucket: {BUCKET_NAME}")
logger.info(f"Local reports: {REPORTS_DIR}")

# --- get remote file list ---
remote_files = {blob.name for blob in bucket.list_blobs()}

# --- upload missing reports ---
local_files = sorted(p for p in REPORTS_DIR.iterdir() if p.is_file())

for lf in local_files:
    if lf.name in remote_files:
        logger.debug(f"UP-TO-DATE: {lf.name}")
        continue

    logger.info(f"UPLOADING: {lf.name}")

    blob = bucket.blob(lf.name)
    blob.upload_from_filename(str(lf))

logger.info("Report sync complete")
