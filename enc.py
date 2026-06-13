from gui import PassCoreUI
from backup import create_backup
import os, struct, json, platform, hashlib, uuid
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from PySide6.QtWidgets import(QApplication, QInputDialog, QLineEdit, QMessageBox, QFileDialog)
from PySide6.QtCore import QTimer
from argon2.low_level import hash_secret_raw, Type

RED = "\033[31m" # ERRORS & REPORT
GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS 
BLUE = "\033[34m" # EXISTING Keys
RESET = "\033[0m"

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
        
def get_cache_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".cache" / "passcore"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCore" / "Cache"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_container_dir()
PASSCORE_DIR = get_PassCore_dir()
CACHE_DIR = get_cache_dir()

CONTAINER_DIR.mkdir(parents=True, exist_ok=True)
PASSCORE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SALT_FILE = PASSCORE_DIR / "vault.salt"
META_FILE = PASSCORE_DIR / "meta.json"
CONFIG_FILE =  PASSCORE_DIR / "config.json"
WORKING_BIN = CACHE_DIR / "passwords.bin"

if not SALT_FILE.exists():
    salt = os.urandom(16)
    with open(SALT_FILE, "wb") as k:
        k.write(salt)
else:
    with open(SALT_FILE, "rb") as k:
        salt = k.read()

def sha256_blob(shafile_path):
    hh = hashlib.sha256() # hash helper to cross check modifixation of any blobs

    with open(shafile_path, "rb") as bsha:
        while chunk := bsha.read(8192): # Read 8KB at a time 
            hh.update(chunk)

    return hh.hexdigest() # return hexadecimal hash string.!

def blob_integrity_verify():
    if not META_FILE.exists():
        raise FileNotFoundError("Metadata file is missing")
        
    with open(META_FILE, "r") as blob_meta:
        vault_meta = json.load(blob_meta)

        expected_blobs = vault_meta["blobs"] # outputs the blob dict from metadata.
        for blob_name in expected_blobs:
            container_id = expected_blobs[blob_name]["container"]
            blob_path = CONTAINER_DIR / container_id / blob_name # existing blobs path
            if not blob_path.exists():
                raise FileNotFoundError(f"Missing blob.: {blob_name}")
            
            actual_size = blob_path.stat().st_size # outputs file size of blobs (each blob)
            expected_size = expected_blobs[blob_name]["size"] # Store size of a blob from metadata.
            if actual_size != expected_size: # Compares the physcially stored blob with metadata blobs sizes.!
                raise ValueError(f"blob size mismatch.: {blob_name}")
            
            expected_hash = expected_blobs[blob_name]["sha256"] # outputs stored hash of existing blob
            actual_hash = sha256_blob(blob_path) # generate hash for existing blob
            if actual_hash != expected_hash:
                raise ValueError(f"Hash mismatch.: {blob_name}")
            
        actual_blobs = len(vault_meta["blobs"])
        
        if actual_blobs != vault_meta["blob_count"]:
            raise ValueError("blob count mismatch.!")

def merge_blob_bin():
    with open(META_FILE, "r") as meta_ctn:
        meta = json.load(meta_ctn)
    
    with open(WORKING_BIN, "wb") as dst_bin:
        for blob_name in sorted(meta["blobs"]):
            container_id = meta["blobs"][blob_name]["container"] 
            blob_path = CONTAINER_DIR / container_id / blob_name
            
            if not blob_path.exists():
                raise FileNotFoundError(f"Missing blob {blob_name}")

            with open(blob_path, "rb") as src_blob: # Merge all the blobs exists in PASSCORE_DIR to generate bin cache for after use in Decryption.!
                dst_bin.write(src_blob.read())

def split_file_bin(file_bin, chunk_size=32):
    for exist_blob in CONTAINER_DIR.iterdir():
        if exist_blob.name.startswith("blob_") and exist_blob.suffix == ".bin":
            print(f"{BLUE}DELETING_existing {exist_blob.name}{RESET}")
            os.remove(CONTAINER_DIR / exist_blob) # Remove existing blobs to prevent corrupt reconstruction while merging files for decrypt.!

    print(f"\n{GREEN}splitting {file_bin.name}......{RESET}")
    with open(WORKING_BIN, "rb") as src_bin:
        index = 0

        blob_info = {}
        while True:
            chunk = src_bin.read(chunk_size)
            if not chunk:
                break
            
            container_id = uuid.uuid4().hex[:16]
            container_path = CONTAINER_DIR / container_id
            container_path.mkdir(parents=True, exist_ok=True)
            
            path = (container_path / f"blob_{index:04d}.bin").resolve()
            print(f"{path.name} Chunk Size: {len(chunk)} bytes")
            with open(path, "wb") as blob_dst: # write data for splitting bin data to blobs 
                blob_dst.write(chunk)
            
            blob_info[path.name] = {
                "container": container_id
            }
            index += 1
        
        return blob_info

def encrypt_vault(new_lines, key): # Encrypt raw bytes
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption

    with open(WORKING_BIN, "wb") as encrypt_bin:
        for i, line in enumerate(new_lines):
            line = line.strip()

            nonce = os.urandom(12)
            encrypt_enc_d = enc_cipher.encrypt(nonce, line.encode(), None) # Encrypt string to bytes
            record_enc_d = nonce + encrypt_enc_d
            length = len(record_enc_d)

            encrypt_bin.write(struct.pack(">I", length)) # store encrypted raw bytes length
            encrypt_bin.write(record_enc_d) # store encrypted raw bytes record with nonce
            # print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    if WORKING_BIN.exists():
        split_file_bin(WORKING_BIN, chunk_size=32)
    
    if META_FILE.exists():
        with open(META_FILE, "r") as meta_js:
            vault_meta = json.load(meta_js)
    else:
        vault_meta = {}
    
    blob_info = split_file_bin(WORKING_BIN, chunk_size=32) 
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    blob_data = {}
    total_size = 0
    for blob_name, info in blob_info.items():
        container_id = info["container"]
        blob_path = CONTAINER_DIR / container_id / blob_name
        if Path(blob_name).match("blob_*.bin"):
            size = blob_path.stat().st_size
            blob_data[blob_name] = {
                "container": container_id,
                "size": size,
                "sha256": sha256_blob(blob_path)
            }
            total_size += size
    print("================================================")
    print(f"Working bin: {WORKING_BIN.stat().st_size} bytes")
    print(f"Total blob size: {total_size} bytes")
    print("================================================")
    
    with open(META_FILE, "r") as old_meta:
        created_at = json.load(old_meta)
    vault_meta = {
        "storage_path": str(CONTAINER_DIR),
        "created": created_at["created"],
        "modified": timestamp,
        "total_size": total_size,
        "blob_count": len(blob_data),
        "blobs": blob_data
    }
    with open(META_FILE, "w") as json_update:
        json.dump(vault_meta, json_update, indent=4)
    
    print("Saved.!\n")
    
    print(f"removed : {WORKING_BIN}...")
    os.remove(WORKING_BIN)

def decrypt_vault(key):
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption
    vault_lines = []
    file_bin = WORKING_BIN
    try:
        if not WORKING_BIN.exists():
            print(f"{RED}Vault exists but salt-key or passwords blob is missing.\nThe vault cannot be decrypted.!{RESET}")
            QMessageBox.information(None, "PassCore", "No vault found.!\nCreating a new vault.!")
            return []

        else:
            print(f"{GREEN}File in working directory: {RESET}",file_bin.name.capitalize(), "\n")

            with open(file_bin, "rb") as decrypt_bin:
                while True:
                    read_len_data = decrypt_bin.read(4) # Read 4 byte length
                    if not read_len_data:
                        break

                    length = struct.unpack(">I", read_len_data)[0] # Unpack lenght integer bytes
                    record_enc_d = decrypt_bin.read(length) # Read full byte record
                    nonce, cipher_text = record_enc_d[:12], record_enc_d[12:] # Extract nonce and Cipher text
                    decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string
                    vault_lines.append(decrypt_enc_d.decode())
                
    except FileNotFoundError as e1:
        print(f"{RED}Error: {RESET}", e1)
    
    return vault_lines

def vault_lock(window, editor, save_btn, unlock_btn, lock_btn):
    reply = QMessageBox.question(
        window, "PassCore", "Lock the vault.?", QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        if WORKING_BIN.exists():
            os.remove(WORKING_BIN)
        editor.setPlainText(window.lock_screen)
        editor.setReadOnly(True)
        window.status_label.setText("Locked")

        lock_btn.setEnabled(False)
        save_btn.setEnabled(False)
        unlock_btn.setEnabled(True)
        QMessageBox.information(window, "PassCore", "Vault Locked.!")

        unlock_btn.show()
        window.key = None 
        
    elif reply == QMessageBox.No:
        return

def is_first_run():
    return not META_FILE.exists()

def init_vault(window):
    vault_meta = {}
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    blob_data = {}
    total_size = 0
    vault_meta = {
        "storage_path": str(CONTAINER_DIR),
        "created": timestamp,
        "modified": timestamp,
        "total_size": total_size,
        "blob_count": len(blob_data),
        "blobs": blob_data
        }
    
    with open(META_FILE, "w") as meta_f:
        json.dump(vault_meta, meta_f, indent=4)

def vault_exists():
    if not PASSCORE_DIR.is_dir():
        return False
    
    if not SALT_FILE.exists():
        return False

    if not META_FILE.exists():
        is_first_run()

    with open(META_FILE, "r") as meta_ctn:
        meta = json.load(meta_ctn)
        
    return len(meta["blobs"]) > 0

def unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn):
    while True:
        if is_first_run():            
            init_vault(window)
            masterpasswd, ok = QInputDialog.getText(
                window, "Unlock Vault",
                f"Set your master password: ", QLineEdit.Password
            )
            if not ok:
                window.close()
                return
            
            # Generates key for first run.!
            key = hash_secret_raw(
                secret=masterpasswd.encode(),
                salt=salt, # Random values
                time_cost=3, # No. of iterations
                memory_cost=65536, # 64MB Argon memory hardness
                parallelism=4, # No. of system threads/lanes
                hash_len=32, # Output size, in bytes 32bytes = 256bits
                type=Type.ID # I : Designed against side-channel attacks, D : Designed against GPU attacks for passwords
            ) 
            window.key = key
            editor.show()
            save_btn.show()
            close_btn.show()
            lock_btn.show()
            unlock_btn.hide()

            editor.clear()
            editor.setReadOnly(False)
            window.status_label.setText("Unlocked")
            save_btn.setEnabled(True)
            lock_btn.setEnabled(True)

            QMessageBox.information(
                window, "PassCore", "Create your first vault"
            )
            return

        if not vault_exists():
            QMessageBox.information(
                window, "PassCore vault", "vault data is missing or corrupted.!"
            )
            return

        try:
            try:
                blob_integrity_verify()
            except (FileNotFoundError, ValueError) as e:
                window.vault_corrupted()
                QMessageBox.information(window, "PassCore", str(e))
                return
            merge_blob_bin()

        except FileNotFoundError:
            QMessageBox.information(
                window, "PassCore vault", "vault blobs are missing..."
            )
            return
        
        masterpasswd, ok = QInputDialog.getText(
            window, "Unlock Vault",
            f"Master Passwd: ", QLineEdit.Password
        )
        
        if not ok:
            window.close()
            return
        
        # key for unlock and authenticate vault blobs
        key = hash_secret_raw(
            secret=masterpasswd.encode(),
            salt=salt, # Random values
            time_cost=3, # No. of iterations
            memory_cost=65536, # 64MB Argon memory hardness
            parallelism=4, # No. of system threads/lanes
            hash_len=32, # Output size, in bytes 32bytes = 256bits
            type=Type.ID # I : Designed against side-channel attacks, D : Designed against GPU attacks for passwords
        ) 
        window.key = key
        try:
            vault_lines = decrypt_vault(key)
            
            unlock_btn.hide()
            
            editor.show()
            save_btn.show()
            close_btn.show()
            lock_btn.show()
            editor.setPlainText("\n".join(vault_lines))
            editor.setReadOnly(False)
            window.status_label.setText("Unlocked")

            save_btn.setEnabled(True)
            lock_btn.setEnabled(True)
            return
        
        except InvalidTag:
            QMessageBox.information(window, "PassCore", "wrong master password.!")

def autosave_vault(window, editor):
    if window.key is None:
        return
    
    save_vault(window, editor, window.key)

def save_vault(window, editor, key):
    new_lines = editor.toPlainText().splitlines()
    create_backup()
    encrypt_vault(new_lines, key)
    timestamp = datetime.now().strftime("%H:%M:%S")
    window.save_label.setText(
        f"Last Save\n{timestamp}"
    )
    QMessageBox.information(None, "PassCore", "Vault saved successfully.!")

def vault_close(window, editor, key):
    reply = QMessageBox.question(
        window, "PassCore", "Save changes before closing the Vault.?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
    )
    if reply == QMessageBox.Yes:
        new_lines = editor.toPlainText().splitlines()
        encrypt_vault(new_lines, key)
        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.No:
        if WORKING_BIN.exists():
            os.remove(WORKING_BIN)

        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.Cancel:
        return

def user_edit():
    app = QApplication([])
    window = PassCoreUI()
    window.key = None
    editor = window.editor
    
    save_btn = window.save_btn
    close_btn = window.close_btn
    lock_btn = window.lock_btn
    unlock_btn = window.unlock_btn

    window.save_btn.clicked.disconnect()
    window.close_btn.clicked.disconnect()

    autosave_timer = QTimer() # Autosave Timer 
    autosave_timer.setSingleShot(True) # Trigger autosave timer : True
    editor.textChanged.connect(
        lambda: autosave_timer.start(60000) # Set autosave timer for 60s(1 min) if changes appear in Editor.
    )
    autosave_timer.timeout.connect(
        lambda: autosave_vault(window, editor) # triggers autosave_vault() when key is None
    )
    
    unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    
    save_btn.clicked.connect(
        lambda: save_vault(window, editor, window.key)
    )

    close_btn.clicked.connect(
        lambda: vault_close(window, editor, window.key))
    
    lock_btn.clicked.connect(
        lambda: vault_lock(window, editor, save_btn, unlock_btn, lock_btn)
    )
    unlock_btn.clicked.connect(
        lambda: unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    )
    window.show()
    app.exec()

user_edit()
