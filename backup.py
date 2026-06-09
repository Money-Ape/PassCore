import os, zipfile, platform
from datetime import datetime
from pathlib import Path

GREEN = "\033[32m" # SUCCESS & NEW RECORDS
RESET = "\033[0m"

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
SALT_FILE = PASSCORE_DIR / "vault.salt"
META_FILE = PASSCORE_DIR / "meta.json"

def create_backup():
    backup_root = Path.home() / "Documents" / "PassCore Backups" # PassCore Backups root
    backup_root.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%d%m%Y%H%M")
    zip_dir = backup_root / f"passcore_backup_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_dir, "w", compression=zipfile.ZIP_DEFLATED) as backto_zip: # writes splitted blobs into zipfile for backup
        backto_zip.write(SALT_FILE, arcname=SALT_FILE.name)
        backto_zip.write(META_FILE, arcname=META_FILE.name)
        for blob in PASSCORE_DIR.iterdir():
            if blob.match("blob_*.bin"):
                backto_zip.write(blob, arcname=blob.name)
    
    MAX_BACKUPS = 10
    all_backups = sorted(backup_root.glob("*.zip"))
    while len(all_backups) > MAX_BACKUPS:
        old_backup = all_backups.pop(0)
        old_backup.unlink()

    print(f"\nBackup Created[{GREEN}{zip_dir}{RESET}]")

def restore_backup():
    backupzip_dir = Path.home() / "Documents" / "PassCore Backups"
    zip_frompath = sorted(backupzip_dir.iterdir(), reverse=True)

    if not zip_frompath:
        print("no backups found.!")
        return
    else:
        latest_backups = zip_frompath[0]
        
        for file in PASSCORE_DIR.iterdir(): # Removes existing corrupted vault from PASSCORE_DIR
            if (file.match("blob_*.bin")
                or file.name == SALT_FILE
                or file.name == META_FILE
                ):
                file.unlink()
        with zipfile.ZipFile(latest_backups, "r") as backfrom_zip:
            backfrom_zip.extractall(PASSCORE_DIR)

    print(f"Recovered from {latest_backups.name}")
