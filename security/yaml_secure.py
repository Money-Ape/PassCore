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