import json
import shutil
import os
from pathlib import Path

def clean_directory(directory_path):
    """
    Removes all files and subdirectories from the given directory path.
    Does not remove the directory itself.
    """
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Directory not found, skipping: {directory}")
        return

    print(f"Cleaning: {directory}")
    for item in directory.iterdir():
        try:
            if item.name == ".gitkeep":
                 continue
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"Failed to delete {item}. Reason: {e}")

def main():
    # Resolve the project root relative to this script
    # Script is in scr/storage/cleaner.py 
    # path: .../SHM_SA_reporter/scr/storage/cleaner.py
    # parents[0] = storage
    # parents[1] = scr
    # parents[2] = SHM_SA_reporter (Root)
    
    script_path = Path(__file__).resolve()
    project_root = script_path.parents[2]
    
    config_path = project_root / "config/path.json"
    
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        return

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config: {e}")
        return

    # Directories to clean as requested
    keys_to_clean = ["parquet_dir", "plots_dir", "report_dir"]
    
    for key in keys_to_clean:
        dir_rel_path = config.get(key)
        if dir_rel_path:
            full_path = project_root / dir_rel_path
            clean_directory(full_path)
        else:
            print(f"Warning: Key '{key}' not found in config")

    print("Cleanup complete.")

if __name__ == "__main__":
    main()
