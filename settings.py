import json, os, platform
from pathlib import Path

def get_PassCore_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / "passcore"
    
    elif sys == "Windows":
        return Path(os.getenv("APPDATA")) / "PassCore"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

PASSCORE_DIR = get_PassCore_dir()
PASSCORE_DIR.mkdir(parents=True, exist_ok=True)
SETTING_FILE =  PASSCORE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "auto_lock_min": 5,
    "theme": "default",
    "hide_from_capture": False,
    "storage_mode": "default"
}

def load_settings():
    if not SETTING_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTING_FILE, "r", encoding="utf-8") as load_file:
            return json.load(load_file)
    
    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
def save_settings(settings):
    with open(SETTING_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)
