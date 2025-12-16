import boto3
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from botocore.exceptions import ClientError

load_dotenv()

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

# === PATHS ===
ROOT = Path(__file__).resolve().parents[2]
PATHS = json.loads((ROOT / "config/path.json").read_text())
FILES = list((ROOT / PATHS["parquet_dir"]).rglob("*"))


def object_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise  # real error


# # === UPLOAD LOOP ===
# for p in FILES:
#     if not p.is_file() or p.suffix != ".parquet":
#         continue

#     name = p.name                  # 2025W49_sst_hub2.parquet
#     folder = name[8:-8]            # sst_hub2 / fft_hub1 / accel_all
#     key = f"{folder}/{name}"

#     if object_exists(R2_BUCKET, key):
#         print(f"✔ EXISTS → {key}")
#         continue

#     print(f"⬆ UPLOADING → {key}")

#     s3.upload_file(
#         Filename=str(p),
#         Bucket=R2_BUCKET,
#         Key=key,
#     )

print("✅ Parquet sync complete.")
