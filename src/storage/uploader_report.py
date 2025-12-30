import os
import json
from pathlib import Path
from ftplib import FTP
from dotenv import load_dotenv

load_dotenv()

# --- FTP config ---
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_BASE_DIR = os.getenv("FTP_BASE_DIR", "/")

# --- repo root ---
ROOT = Path(__file__).resolve().parents[2]

# --- load paths ---
with open(ROOT / "config/path.json") as f:
    PATHS = json.load(f)

REPORTS_DIR = ROOT / PATHS["report_dir"]

if not REPORTS_DIR.exists():
    raise FileNotFoundError(f"Reports dir not found: {REPORTS_DIR}")

# --- connect to FTP ---
ftp = FTP(FTP_HOST, timeout=15)
ftp.login(FTP_USER, FTP_PASS)
ftp.cwd(FTP_BASE_DIR)

print(f"✔ Connected to FTP: {FTP_HOST}")
print(f"📂 Remote dir: {FTP_BASE_DIR}")
print(f"📁 Local reports: {REPORTS_DIR}\n")

# --- get remote file list ---
remote_files = set()
ftp.retrlines("NLST", remote_files.add)

# --- upload missing reports ---
local_files = sorted(p for p in REPORTS_DIR.iterdir() if p.is_file())

for lf in local_files:
    if lf.name in remote_files:
        print(f"✔ UP-TO-DATE: {lf.name}")
        continue

    print(f"⬆ UPLOADING: {lf.name}")

    with open(lf, "rb") as f:
        ftp.storbinary(f"STOR {lf.name}", f)

print("\n✅ Report sync complete")
ftp.quit()

