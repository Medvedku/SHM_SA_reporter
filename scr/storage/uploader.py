import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

# === R2 CONFIG ===
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT   = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET     = os.getenv("R2_BUCKET")

# === S3 CLIENT ===
s3 = boto3.client(
    "s3",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    endpoint_url=R2_ENDPOINT,
)

from pathlib import Path
import json

ROOT = Path.cwd().parents[1]
PATHS = json.loads((ROOT / "config/path.json").read_text())
FILES = list((ROOT / PATHS["parquet_dir"]).rglob("*"))

for p in FILES:
    if not p.is_file():
        continue

    if p.suffix != ".parquet":
        continue

    name = p.name                      # 2025W49_sst_hub2.parquet
    folder = name[8:-8]                # sst_hub2 / fft_hub1 / accel_all
    key = f"{folder}/{name}"           # R2 object key

    print(f"⬆ {name} → {key}")

    s3.upload_file(
        Filename=str(p),
        Bucket=R2_BUCKET,
        Key=key,
    )

print("✅ ALL parquets uploaded.")
