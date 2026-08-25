@echo off
setlocal enabledelayedexpansion

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

python -c "import cryptography,argon2,PySide6,PIL,yaml" 2>NUL

if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install cryptography argon2-cffi PySide6 pillow PyYAML
)

rem Build the PassCore.Utilities C# bridge if it hasn't been published yet.
set "UTIL_DIR=utilities\PassCore.Utilities"

if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "RID=win-arm64"
) else (
    set "RID=win-x64"
)

set "UTIL_BIN=%UTIL_DIR%\publish\%RID%\PassCore.Utilities.exe"

if not exist "%UTIL_BIN%" (
    where dotnet >NUL 2>NUL
    if errorlevel 1 (
        echo Warning: .NET SDK not found. Skipping PassCore.Utilities build.
        echo Install the .NET SDK to enable backups, vault import/export, and health checks.
    ) else (
        echo PassCore.Utilities not found for %RID%, building...
        dotnet publish "%UTIL_DIR%" -c Release -r %RID% --self-contained -o "%UTIL_DIR%\publish\%RID%"
        if errorlevel 1 (
            echo Warning: Failed to build PassCore.Utilities.
            echo Backups, vault import/export, and health checks will be unavailable.
        )
    )
)

echo Launching PassCore...
python enc.py

pause