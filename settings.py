import os, platform, yaml
from pathlib import Path
from security.yaml_secure import secure_load, validate_settings, VaultValidationError

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
SETTING_FILE = PASSCORE_DIR / "settings.yaml"

DEFAULT_SETTINGS = {
    "auto_lock_min": 5,
    "theme": "default",
    "hide_from_capture": False,
    "storage_mode": "default",

    "security": {
        "strict": True,
        "max_entries": 10000,
        "max_blob_size": 1048576
    }
}

def load_settings():
    if not SETTING_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTING_FILE, "r", encoding="utf-8") as load_file:
            content = load_file.read()

        settings = secure_load(content)
        validate_settings(settings)
        return settings

    except (VaultValidationError, yaml.YAMLError, OSError) as e:

        print(f"[Settings] Invalid settings.yaml: {e}")
        print("[Settings] Restoring default settings.")

        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    except Exception as e:
        print(f"[Settings] Failed to load settings: {e}")
        print("[Settings] Restoring default settings.")
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
def save_settings(settings):
    validate_settings(settings)
    with open(SETTING_FILE, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            settings,
            file,
            sort_keys=False,
            default_flow_style=False
        )