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
    "PySide6" : "PySide6",
    "PIL" : "pillow",
    "yaml" : "PyYAML"
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

# Build the PassCore.Utilities C# bridge if it hasn't been published yet.
UTIL_DIR="utilities/PassCore.Utilities"
MACHINE=$(uname -m)

case "$MACHINE" in
    x86_64|amd64)
        RID="linux-x64"
        ;;
    aarch64|arm64)
        RID="linux-arm64"
        ;;
    *)
        echo "Warning: Unsupported architecture '$MACHINE', skipping utility build."
        RID=""
        ;;
esac

if [ -n "$RID" ]; then
    UTIL_BIN="$UTIL_DIR/publish/$RID/PassCore.Utilities"

    if [ ! -f "$UTIL_BIN" ]; then
        if command -v dotnet >/dev/null 2>&1; then
            echo "PassCore.Utilities not found for $RID, building..."
            dotnet publish "$UTIL_DIR" -c Release -r "$RID" --self-contained true -p:PublishSingleFile=true -p:PublishTrimmed=false -o "$UTIL_DIR/publish/$RID" || {
                echo "Warning: Failed to build PassCore.Utilities."
                echo "Backups, vault import/export, and health checks will be unavailable."
            }
        else
            echo "Warning: .NET SDK not found. Skipping PassCore.Utilities build."
            echo "Install the .NET SDK to enable backups, vault import/export, and health checks."
        fi
    fi
fi

echo "Initializing..."
python3 enc.py