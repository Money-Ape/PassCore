import os, zipfile, platform, shutil, threading
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox

GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS
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
SETTINGS = PASSCORE_DIR / "settings.json"
IMAGES_META = PASSCORE_DIR / "images_index.json"

BACKUP_ROOT = Path.home() / "Documents" / "PassCore Backups" # PassCore Backups root
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

vault_changed = False
def _create_backup(force=False, finished_callback=None):
    global vault_changed
    if not force and not vault_changed:
        return

    try:
        timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
        zip_dir = BACKUP_ROOT / f"passcore_backup_{timestamp}.zip"

        print(f"_create_backup(force={force}, vault_changed={vault_changed})\nCreating Backup[{GREEN}{zip_dir.name}{RESET}]")
        with zipfile.ZipFile(zip_dir, "w", compression=zipfile.ZIP_DEFLATED) as backto_zip: # writes splitted blobs into zipfile for backup
            backto_zip.write(SALT_FILE, arcname=SALT_FILE.name)
            backto_zip.write(META_FILE, arcname=META_FILE.name)
            backto_zip.write(SETTINGS, arcname=SETTINGS.name)
            backto_zip.write(IMAGES_META, arcname=IMAGES_META.name)

            for file in CONTAINER_DIR.rglob("*"):
                if file.is_file():
                    backto_zip.write(file, arcname=file.relative_to(CONTAINER_DIR))

        vault_changed = False # Processing the pending backup.

        MAX_BACKUPS = 10
        all_backups = sorted(BACKUP_ROOT.glob("*.zip"))
        while len(all_backups) > MAX_BACKUPS:
            old_backup = all_backups.pop(0)
            old_backup.unlink()

        print(f"Exists: {YELLOW}{zip_dir.exists()}{RESET}")
        print(f"\nBackup Created[{GREEN}{zip_dir}{RESET}]")
        print(f"Size: {YELLOW}{zip_dir.stat().st_size}{RESET} bytes")

        if finished_callback:
            finished_callback(True)

    except Exception as e:
        print(f"[Backup Error: {e}]")
        vault_changed = True
        if finished_callback:
            finished_callback(False)

backup_thread = None
def create_backup(force=False, finished_callback=None):
    print("initiating backup...")
    global backup_thread
    if backup_thread and backup_thread.is_alive():
        print("Backup already running.!")
        return
    
    backup_thread = threading.Thread(
        target=_create_backup,
        kwargs={
            "force": force,
            "finished_callback": finished_callback
        },
        daemon=True,
        name="PassCore Backup")
    backup_thread.start()

def restore_backup(window):
    global vault_changed
    backupzip_dir = Path.home() / "Documents" / "PassCore Backups"

    backup_file, _ = QFileDialog.getOpenFileName(
        window, "Select Backup Zip", str(backupzip_dir), "", "Zip archives (*.zip)",
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
        shutil.move(CONTAINER_DIR / "settings.json", PASSCORE_DIR)
        shutil.move(CONTAINER_DIR / "images_index.json", PASSCORE_DIR)

    print(f"Recovered from {backup_file.name}")

    window.key = None
    window.editor.setPlainText(window.lock_screen)
    window.editor.setReadOnly(True)
    window.status_label.setText("Locked")
    window.lock_btn.hide()
    window.unlock_btn.setEnabled(True)
    window.unlock_btn.show()
    window.save_btn.hide()
    window.close_btn.setEnabled(True)

    QMessageBox.information(window, "PassCore Restore", "Backup restored successfully.!\n\nUnlock the restored vault to continue.!")
    vault_changed = True
