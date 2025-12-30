import json
import shutil
import os
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_directory(directory_path):
    """
    Removes all files and subdirectories from the given directory path.
    Does not remove the directory itself.
    """
    directory = Path(directory_path)
    if not directory.exists():
        logger.warning(f"Directory not found, skipping: {directory}")
        return

    logger.info(f"Cleaning: {directory}")
    for item in directory.iterdir():
        try:
            if item.name == ".gitkeep":
                continue
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            logger.error(f"Failed to delete {item}. Reason: {e}")


def main():
    # Resolve the project root relative to this script
    # Script is in src/storage/cleaner.py
    # path: .../SHM_SA_reporter/src/storage/cleaner.py
    # parents[0] = storage
    # parents[1] = src
    # parents[2] = SHM_SA_reporter (Root)

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]

    config_path = project_root / "config/path.json"
    
    if not config_path.exists():
        logger.error(f"Config file not found at {config_path}")
        return    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return

    # Directories to clean as requested
    keys_to_clean = ["parquet_dir", "plots_dir", "report_dir"]

    for key in keys_to_clean:
        dir_rel_path = config.get(key)
        if dir_rel_path:
            full_path = project_root / dir_rel_path
            clean_directory(full_path)
        else:
            logger.warning(f"Key '{key}' not found in config")

    # --- NEW: Specific file cleanup (DuckDB + Emails) ---

    # 1. Clean DuckDB
    duck_dir_rel = config.get("duck_dir")
    if duck_dir_rel:
        duck_db_path = project_root / duck_dir_rel / "shm_report.duckdb"
        if duck_db_path.exists():
            try:
                duck_db_path.unlink()
                logger.info(f"Removed DuckDB file: {duck_db_path}")
            except Exception as e:
                logger.error(f"Failed to remove DuckDB: {e}")

    # 2. Clean Email HTML files in src/mailer/
    # The emailer generates files like email_2025W50.html in src/mailer/

    mailer_dir = project_root / "src/mailer"

    if mailer_dir.exists():
        pattern = re.compile(r"email_\d{4}W\d{2}\.html")

        for email_file in mailer_dir.glob("email_*.html"):
            # Skip templates or non-generated files
            if not pattern.fullmatch(email_file.name):
                continue

            try:
                email_file.unlink()
                logger.info(f"Removed email file: {email_file}")
            except Exception as e:
                logger.error(f"Failed to remove email file {email_file}: {e}"): {e}")

    logger.info("Cleanup complete.")


if __name__ == "__main__":
    main()
