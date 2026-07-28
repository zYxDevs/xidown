import os
import sys
import ctypes
from pathlib import Path

# Base & Data Directories
USER_VIDEOS_DIR = os.path.join(os.path.expanduser("~"), "Videos")
DATA_DIR = os.path.join(USER_VIDEOS_DIR, "xidown")
THUMB_DIR = os.path.join(DATA_DIR, "thumbs")
PREVIEW_DIR = os.path.join(DATA_DIR, "preview_cache")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

def hide_directory(path: str) -> bool:
    """Safely apply hidden attribute to a directory on Windows systems."""
    try:
        if os.name == 'nt' and os.path.exists(path):
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x02) # 0x02 = Hidden
            return True
    except Exception as e:
        print(f"[Config] Failed to hide directory {path}: {e}")
    return False

def ensure_data_directories():
    """Ensure essential directories exist and hidden attributes are set."""
    for directory in [DATA_DIR, THUMB_DIR, PREVIEW_DIR]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"[Config] Error creating directory {directory}: {e}")
    
    # Apply hidden attributes to hidden cache folders
    hide_directory(THUMB_DIR)
    hide_directory(PREVIEW_DIR)

# Initialize directories upon module load
ensure_data_directories()
