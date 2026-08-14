import yaml

MAX_DEPTH = 10
MAX_KEYS = 1000
MAX_STRING = 2048


class VaultValidationError(Exception):
    pass

#----------Safe YAML Loader----------#
def secure_load(yaml_text: str):
    try:
        data = yaml.safe_load(yaml_text)
    except Exception as e:
        raise VaultValidationError(f"YAML parse error: {e}")

    validate_structure(data)
    return data

#----------Recursive Validator----------#
def validate_structure(data, depth=0):
    if depth > MAX_DEPTH:
        raise VaultValidationError("Max depth exceeded")

    if isinstance(data, dict):
        if len(data) > MAX_KEYS:
            raise VaultValidationError("Too many keys")

        for k, v in data.items():
            if not isinstance(k, str):
                raise VaultValidationError("Non-string key detected")

            if len(k) > 256:
                raise VaultValidationError("Key too long")

            validate_structure(v, depth + 1)

    elif isinstance(data, list):
        if len(data) > MAX_KEYS:
            raise VaultValidationError("List too large")

        for item in data:
            validate_structure(item, depth + 1)

    elif isinstance(data, str):
        if len(data) > MAX_STRING:
            raise VaultValidationError("String too long")

    elif isinstance(data, (int, float, bool, type(None))):
        return

    else:
        raise VaultValidationError(f"Unsupported type: {type(data)}")

def validate_settings(settings):
    if not isinstance(settings, dict):
        raise VaultValidationError("Settings root must be a mapping.")

    allowed_keys = {
        "auto_lock_min",
        "theme",
        "hide_from_capture",
        "storage_mode",
        "security"
    }
    unknown_keys = set(settings) - allowed_keys
    if unknown_keys:
        raise VaultValidationError(
            f"Unknown settings: {', '.join(sorted(unknown_keys))}"
        )

    # -----------------------------
    # auto_lock_min
    # -----------------------------
    auto_lock_min = settings.get("auto_lock_min")

    if not isinstance(auto_lock_min, int) or isinstance(auto_lock_min, bool):
        raise VaultValidationError(
            "auto_lock_min must be an integer."
        )

    if not 0 <= auto_lock_min <= 1440:
        raise VaultValidationError(
            "auto_lock_min must be between 0 and 1440."
        )

    # -----------------------------
    # theme
    # -----------------------------
    theme = settings.get("theme")

    if not isinstance(theme, str):
        raise VaultValidationError(
            "theme must be a string."
        )

    allowed_themes = {
        "default",
        "cozy_pink",
        "soft_blossom",
        "catppuccin",
        "slate_grey",
        "forest",
        "beige",
        "mint_green",
        "sage_green",
        "tokyo_night",
        "nord",
        "ivory",
        "cream_darkgrey",
        "sage_darkgrey",
        "blue_gray_black",
        "charcoal"
    }
    if theme not in allowed_themes:
        raise VaultValidationError(
            f"Unknown theme: {theme}"
        )

    # -----------------------------
    # hide_from_capture
    # -----------------------------
    hide_from_capture = settings.get("hide_from_capture")

    if not isinstance(hide_from_capture, bool):
        raise VaultValidationError(
            "hide_from_capture must be true or false."
        )

    # -----------------------------
    # storage_mode
    # -----------------------------
    storage_mode = settings.get("storage_mode")

    if not isinstance(storage_mode, str):
        raise VaultValidationError(
            "storage_mode must be a string."
        )

    allowed_storage_modes = {
        "default"
    }

    if storage_mode not in allowed_storage_modes:
        raise VaultValidationError(
            f"Unknown storage_mode: {storage_mode}"
        )

    # -----------------------------
    # security
    # -----------------------------
    security = settings.get("security", {})

    if not isinstance(security, dict):
        raise VaultValidationError(
            "security must be a mapping."
        )

    allowed_security_keys = {
        "strict",
        "max_entries",
        "max_blob_size"
    }
    unknown_security_keys = set(security) - allowed_security_keys
    if unknown_security_keys:
        raise VaultValidationError(
            f"Unknown security settings: "
            f"{', '.join(sorted(unknown_security_keys))}"
        )

    strict = security.get("strict", True)
    if not isinstance(strict, bool):
        raise VaultValidationError(
            "security.strict must be true or false."
        )

    max_entries = security.get("max_entries", 10000)
    if not isinstance(max_entries, int) or isinstance(max_entries, bool):
        raise VaultValidationError(
            "security.max_entries must be an integer."
        )

    if not 1 <= max_entries <= 1_000_000:
        raise VaultValidationError(
            "security.max_entries must be between 1 and 1000000."
        )

    max_blob_size = security.get("max_blob_size", 1048576)
    if not isinstance(max_blob_size, int) or isinstance(max_blob_size, bool):
        raise VaultValidationError(
            "security.max_blob_size must be an integer."
        )

    if not 1024 <= max_blob_size <= 1_073_741_824:
        raise VaultValidationError(
            "security.max_blob_size must be between 1KB and 1GB."
        )

    return True

def convert_yaml_to_text(data):
    lines = []

    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            lines.append(str(item))
    else:
        lines.append(str(data))

    return "\n".join(lines)