#!/usr/bin/bash

if [ ! -d "venv" ]; then
    echo "virtual environment not found.!"
    echo "creating venv..."

    python3 -m venv venv || {
        echo "Failed to create venv."
        exit 1
    }
fi

source venv/bin/activate

python3 - << 'EOF'
import importlib, subprocess, sys

modules = {
    "cryptography" : "cryptography",
    "argon2" : "argon2-cffi",
    "PySide6" : "PySide6"
}

missing = []
for module, package in modules.items():
    try:
        importlib.import_module(module)
    
    except ImportError:
        missing.append(package)

if missing:
    print(f"Installing... {' '.join(missing)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

EOF

echo "Initializing..."
python3 enc*.py
