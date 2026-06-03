#!/usr/bin/bash

modules=$(python - << 'EOF'
import importlib, sys

modules = ["cryptography", "argon2"]
missing = []
for mod in modules:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(mod)
        print(f"\n{mod}.....missing")
if missing:
    sys.exit(1)
sys.exit(0)
EOF
)

modules_missing=$?

if [ -f /etc/os-release ]; then
    . /etc/os-release
    System_ID="$ID"

    echo -e "\nSystem: $System_ID[$NAME]\n"
    if [ "$System_ID" = "arch" ]; then
        if [ $modules_missing -ne 0 ]; then
            sudo pacman -Syy python-cryptography \
            python-argon2-cffi \
            python-argon2-cffi-bindings
        else
            echo "Initializing....."
        fi

    elif [ "$System_ID" = "debian" ] || [ "$System_ID" = "ubuntu" ]; then
        if [ $modules_missing -ne 0 ]; then
            sudo apt-get update; sudo apt-get install python3-cryptography \
            python3-argon2
        else
            echo "Initializing....."
        fi
    else
        echo "You ain't dumb than your machine.! right.?"
    fi
fi

python enc*.py