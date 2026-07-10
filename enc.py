from gui import PassCoreUI, PasswordDialog, QIcon
from backup import create_backup, secure_del_tree
import os, struct, json, platform, hashlib, uuid, base64, sys, ctypes, backup
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from PySide6.QtWidgets import(QApplication, QMessageBox)
from PySide6.QtCore import QTimer
from argon2.low_level import hash_secret_raw, Type
from pcvmenu.images import preview_cache, merge_cache

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

IMAGE_PATH = resource_path("pcvmenu/images.py")

RED = "\033[31m" # ERRORS & REPORT
GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS 
BLUE = "\033[34m" # EXISTING Keys
RESET = "\033[0m"

def get_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db" / "notes"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData" / "notes"
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
    
    merge_data = bytearray()
    for blob_name in sorted(meta["blobs"]):
        container_id = meta["blobs"][blob_name]["container"] 
        blob_path = CONTAINER_DIR / container_id / blob_name
        
        if not blob_path.exists():
            raise FileNotFoundError(f"Missing blob {blob_name}")

        with open(blob_path, "rb") as src_blob: # Merge all the blobs exists in PASSCORE_DIR to generate bin cache for after use in Decryption.!
            merge_data.extend(src_blob.read())
    
    return bytes(merge_data)

def split_file_bin(encrypted_data, chunk_size=32):
    blob_info = {}
    index = 0
    
    for offset in range(0, len(encrypted_data), chunk_size):
        chunk = encrypted_data[offset : offset + chunk_size]
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

def encrypt_vault(notes, key): # Encrypt raw bytes
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption

    encrypted_data = bytearray()

    payload = json.dumps(notes, ensure_ascii=False).encode()

    nonce = os.urandom(12)
    encrypt_enc_d = enc_cipher.encrypt(nonce, payload, None) # Encrypt string to bytes
    record_enc_d = nonce + encrypt_enc_d
    length = len(record_enc_d)

    encrypted_data.extend(struct.pack(">I", length)) # store encrypted raw bytes length
    encrypted_data.extend(record_enc_d) # store encrypted raw bytes record with nonce
    print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    blob_info = split_file_bin(bytes(encrypted_data), chunk_size=32)
    if not blob_info:
        raise RuntimeError("No blobs generated.!")

    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
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
    print(f"Working bin: {len(encrypted_data)} bytes")
    print(f"Total blob size: {total_size} bytes")
    print("================================================")
    
    with open(META_FILE, "r") as old_meta:
        compared = json.load(old_meta)
        old_ctn = {
            info["container"]
            for info in compared["blobs"].values()
        }

    vault_meta = {
        "storage_path": str(CONTAINER_DIR),
        "created": compared["created"],
        "modified": timestamp,
        "auth_nonce": compared["auth_nonce"],
        "auth_blob": compared["auth_blob"],
        "verifier_hash": compared["verifier_hash"],
        "total_size": total_size,
        "blob_count": len(blob_data),
        "blobs": blob_data
    }
    with open(META_FILE, "w") as json_update:
        json.dump(vault_meta, json_update, indent=4)
    
    print("Saved.!\n")
    
    for ctn in old_ctn:
        path  = Path(CONTAINER_DIR / ctn)
        if path.exists():
            secure_del_tree(path)
            print(f"{GREEN}REMOVED_EXISTING - {path.name}{RESET}")

def serialize_notes(notes):
    return json.dumps(notes, ensure_ascii=False)

def deserialize_notes(data):
    return json.loads(data)

def decrypt_vault(key, encrypted_blobs):
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption
    try:
        offset = 0
        while offset < len(encrypted_blobs):
            read_len_data = encrypted_blobs[offset : offset + 4] # Read 4 byte length
            offset += 4
            if not read_len_data:
                break

            length = struct.unpack(">I", read_len_data)[0] # Unpack lenght integer bytes
            record_enc_d = encrypted_blobs[offset : offset + length] # Read full byte record
            offset += length
            nonce, cipher_text = record_enc_d[:12], record_enc_d[12:] # Extract nonce and Cipher text
            decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string
            payload = decrypt_enc_d.decode()
            print(f"{BLUE}DECRYPTED_BLOBS {record_enc_d}{RESET}")
            return json.loads(payload)
                
    except FileNotFoundError as e1:
        return InvalidTag("Unable to decrypt the vault.!\n", e1)

def vault_lock(window, editor, save_btn, unlock_btn, lock_btn, close_btn):    
    reply = QMessageBox.question(
        window, "PassCore", "Lock the vault.?", QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        window.note_list.clear()
        window.note_title.clear()
        
        window.current_note = 0
        editor.clear()
        if window.current_section == "credentials":
            editor.show()
            editor.setPlainText(window.lock_screen)
        else:
            editor.hide()
            preview_cache.clear()
            merge_cache.clear()
            window.reset_image_view()
            window.gallery_scroll.hide()
            window.preview_widget.hide()
            
        editor.setReadOnly(True)
        window.status_label.setText("Locked")
        window.add_btn.setEnabled(False)
        window.note_title.setEnabled(False)
        window.slide_menu.setEnabled(False)

        lock_btn.setEnabled(False)
        lock_btn.hide()
        save_btn.setEnabled(False)
        save_btn.hide()
        close_btn.setEnabled(True)
        unlock_btn.setEnabled(True)

        unlock_btn.show()
        window.key = None
        window.autolock_timer.stop()
        
    elif reply == QMessageBox.No:
        return

def is_first_run():
    return not META_FILE.exists()

def has_blobs():
    with open(META_FILE, "r") as meta_ctn:
        read_meta = json.load(meta_ctn)

    return len(read_meta.get("blobs", {})) > 0

def vault_exists():
    
    if not SALT_FILE.exists():
        return False

    if not META_FILE.exists():
        return False
    
    return True

def unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn):
    while True:
        if is_first_run():            
            vault_meta = {}
            timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            total_size = 0
            blob_data = {}

            dialog = PasswordDialog(title="Create Vault", confirm=True)
            ok = dialog.exec()
            if not ok:
                raise SystemExit
            
            masterpasswd = dialog.password.text()
            
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
            auth_nonce = os.urandom(12)
            verifier = os.urandom(32)
            auth_blob = AESGCM(key).encrypt(auth_nonce, verifier, None)
            vault_meta = {
                "storage_path": str(CONTAINER_DIR),
                "created": timestamp,
                "modified": timestamp,
                "auth_nonce": base64.b64encode(auth_nonce).decode(),
                "auth_blob": base64.b64encode(auth_blob).decode(),
                "verifier_hash": hashlib.sha256(verifier).hexdigest(),
                "total_size": total_size,
                "blob_count": len(blob_data),
                "blobs": blob_data
                }
            print(vault_meta["auth_nonce"],"\n", vault_meta["auth_blob"],"\n", vault_meta["verifier_hash"])
            
            with open(META_FILE, "w") as meta_f:
                json.dump(vault_meta, meta_f, indent=4)

            window.key = key
            window.vault_key = key
            editor.show()
            save_btn.show()
            close_btn.show()
            lock_btn.show()
            unlock_btn.hide()
            window.add_btn.setEnabled(True)
            window.note_title.setEnabled(True)
            window.slide_menu.setEnabled(True)

            editor.clear()
            editor.setReadOnly(False)
            if window.current_section == "credentials":
                window.show_credentials()
            else:
                window.show_images()

            window.status_label.setText("Unlocked")
            save_btn.setEnabled(True)
            lock_btn.setEnabled(True)
            
            minutes = window.settings["auto_lock_min"]
            window.autolock_timer.start(minutes * 60 * 1000)

            QMessageBox.information(
                window, "PassCore", "Create your first vault"
            )
            return

        if not vault_exists():
            QMessageBox.information(
                window, "PassCore vault", "vault data is missing or corrupted.!"
            )
            return

        if not has_blobs(): # Open Empty editor to prevent integrity checks with no blobs.!
            dialog = PasswordDialog(title="Unlock Vault", confirm=False)
            ok = dialog.exec()
            if not ok:
                raise SystemExit

            masterpasswd = dialog.password.text()

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
            try:
                with open(META_FILE, "r") as auth:
                    auth_check = json.load(auth)
                d_nonce = base64.b64decode(auth_check["auth_nonce"])
                d_blob = base64.b64decode(auth_check["auth_blob"])
                result = AESGCM(key).decrypt(d_nonce, d_blob, None)

                if hashlib.sha256(result).hexdigest() != auth_check["verifier_hash"]:
                    raise InvalidTag
                QMessageBox.information(window, "PassCore", "Vault is empty.!")

                window.key = key
                window.vault_key = key
                unlock_btn.hide()
                editor.clear()
                editor.setReadOnly(False)
                if window.current_section == "credentials":
                    window.show_credentials()
                else:
                    window.show_images()

                window.notes = [{
                    "title": "Untitled Note",
                    "content": ""
                }]
                if window.current_section == "credentials":
                    window.load_notes(window.notes)

                lock_btn.setEnabled(True)
                save_btn.setEnabled(True)
                close_btn.setEnabled(True)
                
                window.status_label.setText("Unlocked")
                window.add_btn.setEnabled(True)
                window.note_title.setEnabled(True)
                window.slide_menu.setEnabled(True)

                minutes = window.settings["auto_lock_min"]
                window.autolock_timer.start(
                    minutes * 60 * 1000
                )
                return

            except InvalidTag:
                QMessageBox.information(window, "PassCore", "wrong master password.!")
                continue

        try:
            try:
                blob_integrity_verify()
            except (FileNotFoundError, ValueError) as e:
                window.vault_corrupted()
                QMessageBox.information(window, "PassCore", str(e))
                return
            encrypted_blobs = merge_blob_bin()

        except FileNotFoundError:
            QMessageBox.information(
                window, "PassCore vault", "vault blobs are missing..."
            )
            return
        
        dialog = PasswordDialog(title="Unlock Vault", confirm=False)
        ok = dialog.exec()
        if not ok:
            raise SystemExit
        
        masterpasswd = dialog.password.text()
        
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
        window.vault_key = key
        try:
            vault_notes = decrypt_vault(key, encrypted_blobs)
            
            unlock_btn.hide()
            window.add_btn.setEnabled(True)
            window.note_title.setEnabled(True)
            
            editor.show()
            save_btn.show()
            close_btn.show()
            lock_btn.show()
            editor.setReadOnly(False)
            window.notes = vault_notes
            window.current_note = 0
            if window.current_section == "credentials":
                window.show_credentials()
                window.load_notes(window.notes)
            else:
                window.show_images()

            window.status_label.setText("Unlocked")

            save_btn.setEnabled(True)
            lock_btn.setEnabled(True)
            window.slide_menu.setEnabled(True)

            minutes = window.settings["auto_lock_min"]
            window.autolock_timer.start(minutes * 60 * 1000)
            return
        
        except InvalidTag:
            QMessageBox.information(window, "PassCore", "wrong master password.!")

def autosave_vault(window, editor):
    window.save_current_note()
    non_empty_notes = sum(
        1 for note in window.notes
        if note["content"].strip()
    )
    if len(window.notes) == 1 and non_empty_notes == 0:
        return
    
    if window.key is None:
        return
    
    save_vault(window, editor, window.key)
    timestamp = datetime.now().strftime("%I:%M:%S %p")
    window.save_label.setText(
        f"Last Save:\n{timestamp}"
    )

def autolock_vault(window, editor, save_btn, unlock_btn, lock_btn, close_btn):
    window.note_list.clear()
    window.note_title.clear()
    
    window.current_note = 0
    editor.clear()
    if window.current_section == "credentials":
        editor.show()
        editor.setPlainText(window.lock_screen)
    else:
        editor.hide()
        preview_cache.clear()
        merge_cache.clear()
        window.reset_image_view()
        window.gallery_scroll.hide()
        window.preview_widget.hide()
        
    editor.setReadOnly(True)
    window.status_label.setText("Locked")
    window.add_btn.setEnabled(False)
    window.note_title.setEnabled(False)
    window.slide_menu.setEnabled(False)

    lock_btn.setEnabled(False)
    lock_btn.hide()
    save_btn.setEnabled(False)
    save_btn.hide()
    close_btn.setEnabled(True)
    unlock_btn.setEnabled(True)

    unlock_btn.show()
    window.key = None
    window.autolock_timer.stop()

def save_vault(window, editor, key):
    window.save_current_note()
    current_note = window.notes[window.current_note]
    if not current_note["content"].strip():
        QMessageBox.information(window, "PassCore", "Empty vault.!\n\nNothing to save.")
        return
    
    encrypt_vault(window.notes, key)
    backup.vault_changed = True
    create_backup()
    window.update_vault_size()
    timestamp = datetime.now().strftime("%I:%M:%S %p")
    window.save_label.setText(
        f"Last Save\n{timestamp}"
    )
    # QMessageBox.information(None, "PassCore", "Vault saved successfully.!")

def vault_close(window, key):
    reply = QMessageBox.question(
        window, "PassCore", "Save changes before closing the Vault.?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
    )
    if reply == QMessageBox.Yes:
        window.save_current_note()
        non_empty_notes = sum(
            1 for note in window.notes
            if note["content"].strip()
        )
        if len(window.notes) == 1 and non_empty_notes == 0:
            QMessageBox.information(
                window, "PassCore", "Empty vault.!\nNothing to save."
            )
            return
        
        encrypt_vault(window.notes, key)
        window.update_vault_size()
        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.No:
        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.Cancel:
        return

def user_edit():
    myappid = "moneyape.passcore"
    if sys.platform.startswith("win") or sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            myappid
        )
    print("MEIPASS:", getattr(sys, "_MEIPASS", "NOT SET"))
    print("EXISTS:", os.path.exists(resource_path("assets/PassCore.ico")))
    app = QApplication([])
    icon = QIcon(resource_path("assets/PassCore.ico"))

    app.setWindowIcon(icon)
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
    window.note_title.textChanged.connect(
        lambda: autosave_timer.start(60000)
    )
    editor.textChanged.connect(
        lambda: autosave_timer.start(60000) # Set autosave timer for 60s(1 min) if changes appear in Editor.
    )
    autosave_timer.timeout.connect(
        lambda: autosave_vault(window, editor) # triggers autosave_vault() when key is None
    )

    window.autolock_timer.setSingleShot(True)
    editor.textChanged.connect(
        lambda: window.autolock_timer.start(window.settings["auto_lock_min"] * 60 * 1000))
    
    window.autolock_timer.timeout.connect(
        lambda: autolock_vault(window, editor, save_btn, unlock_btn, lock_btn, close_btn)
    )

    unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    
    save_btn.clicked.connect(
        lambda: save_vault(window, editor, window.key)
    )

    close_btn.clicked.connect(
        lambda: vault_close(window, window.key))
    
    lock_btn.clicked.connect(
        lambda: vault_lock(window, editor, save_btn, unlock_btn, lock_btn)
    )
    unlock_btn.clicked.connect(
        lambda: unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    )
    window.show()
    app.exec()

user_edit()
