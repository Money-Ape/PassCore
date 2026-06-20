import os, zipfile, platform, shutil
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QFileDialog

GREEN = "\033[32m" # SUCCESS & NEW RECORDS
RESET = "\033[0m"

def secure_del_file(path):
    if not path.exists():
        return

    size = path.stat().st_size
    with open(path, "rb+") as file:
        file.write(os.urandom(size))
        file.flush()
        os.fsync(file.fileno())
    
    path.unlink()

def secure_del_tree(dir):
    dir = Path(dir)
    if not dir.exists():
        return
    
    files = sorted(dir.rglob("*"), reverse=True)
    for item in files:
        if item.is_file():
            secure_del_file(item)
        
        elif item.is_dir():
            item.rmdir()
        
    dir.rmdir()

def get_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

def get_PassCore_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / "passcore"
    
    elif sys == "Windows":
        return Path(os.getenv("APPDATA")) / "PassCore"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_container_dir()
PASSCORE_DIR = get_PassCore_dir()

CONTAINER_DIR.mkdir(parents=True, exist_ok=True)
PASSCORE_DIR.mkdir(parents=True, exist_ok=True)
SALT_FILE = PASSCORE_DIR / "vault.salt"
META_FILE = PASSCORE_DIR / "meta.json"

BACKUP_ROOT = Path.home() / "Documents" / "PassCore Backups" # PassCore Backups root
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

def create_backup():    
    timestamp = datetime.now().strftime("%d%m%Y%H%M")
    zip_dir = BACKUP_ROOT / f"passcore_backup_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_dir, "w", compression=zipfile.ZIP_DEFLATED) as backto_zip: # writes splitted blobs into zipfile for backup
        backto_zip.write(SALT_FILE, arcname=SALT_FILE.name)
        backto_zip.write(META_FILE, arcname=META_FILE.name)

        for file in CONTAINER_DIR.rglob("*"):
            if file.is_file():
                backto_zip.write(file, arcname=file.relative_to(CONTAINER_DIR))
    
    MAX_BACKUPS = 10
    all_backups = sorted(BACKUP_ROOT.glob("*.zip"))
    while len(all_backups) > MAX_BACKUPS:
        old_backup = all_backups.pop(0)
        old_backup.unlink()

    print(f"\nBackup Created[{GREEN}{zip_dir}{RESET}]")

def restore_backup():
    backupzip_dir = Path.home() / "Documents" / "PassCore Backups"

    backup_file, _ = QFileDialog.getOpenFileName(
        None, "Select Backup Zip", str(backupzip_dir), "", "Zip archives (*.zip)",
        options=QFileDialog.Option.DontUseNativeDialog
        )
    if not backup_file:
        return
    
    backup_file = Path(backup_file)
    if CONTAINER_DIR.exists():
        secure_del_tree(CONTAINER_DIR)
    CONTAINER_DIR.mkdir(parents=True, exist_ok=True) # Will create Empty Dir.
    
    if META_FILE.exists():
        META_FILE.unlink()

    if SALT_FILE.exists():
        SALT_FILE.unlink()

    with zipfile.ZipFile(backup_file, "r") as backfrom_zip:
        backfrom_zip.extractall(CONTAINER_DIR) 
        shutil.move(CONTAINER_DIR / "meta.json", PASSCORE_DIR)
        shutil.move(CONTAINER_DIR / "vault.salt", PASSCORE_DIR)

    print(f"Recovered from {backup_file.name}")
