from PIL import Image
import sys, os, platform, mimetypes, uuid, hashlib, json, struct
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtGui import QPixmap
from datetime import datetime
from io import BytesIO
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

preview_cache = {}
merge_cache = {}
MAX_CACHE = 100

def get_PassCore_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / "passcore"
    
    elif sys == "Windows":
        return Path(os.getenv("APPDATA")) / "PassCore"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")
    
PASSCORE_DIR = get_PassCore_dir()
IMAGES_META = PASSCORE_DIR / "images_index.json"

def get_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db" / "images"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData" / "images"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_container_dir()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

def sha256_blob(shafile_path):
    hh = hashlib.sha256() # hash helper to cross check modifixation of any blobs

    with open(shafile_path, "rb") as bsha:
        while chunk := bsha.read(8192): # Read 8KB at a time 
            hh.update(chunk)

    return hh.hexdigest() # return hexadecimal hash string.!

def import_image(image_path, album_name, vault_key):
    image_path = Path(image_path)
    with Image.open(image_path) as PCi:

        with open(image_path, "rb") as img:
            image_bytes = img.read()

        mime, _ = mimetypes.guess_type(image_path)

        # PASSCORE_DIR images metadata
        image_info = {
            "image_id": uuid.uuid4().hex[:32],
            "image_path": image_path,
            "image_bytes": image_bytes,
            "mime": mime,
            "width": PCi.width,
            "height": PCi.height,
            "mode": PCi.mode,
            "format": PCi.format,
            "sha256": ""
        }

    encrypt_image(image_path, image_info, image_bytes, album_name, vault_key)

def encrypt_image(image_path, image_info, image_bytes, album_name, vault_key):
    enc_cipher = AESGCM(vault_key)
    encrypted_data = bytearray()

    nonce = os.urandom(12)
    encrypted_enc_data = enc_cipher.encrypt(nonce, image_bytes, None) # Encrypt image bytes to encrypte bytes.
    record_enc_data = nonce + encrypted_enc_data
    length = len(record_enc_data)

    encrypted_data.extend(struct.pack(">I", length)) # Store encrypted raw bytes length
    encrypted_data.extend(record_enc_data)

    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    album_id = uuid.uuid4().hex[:32]
    # PASSCORE_DIR images metadata
    image_meta = {
        "albums": {
            album_name: {
                album_id: {
                    image_path.name: {
                        "uuid": image_info["image_id"],
                        "mime": image_info["mime"],
                        "extension": image_path.suffix,
                        "width": image_info["width"],
                        "height": image_info["height"],
                        "size" : len(image_info["image_bytes"]),
                        "sha256": hashlib.sha256(encrypted_data).hexdigest(),
                        "created_at": timestamp,
                    }
                }
            }
        }
    }
    if not IMAGES_META.exists(): # Initially create if IMAGES_META json not exists
        with open(IMAGES_META, "w") as f_init:
            json.dump(image_meta, f_init, indent=4)

        split_image_bin(image_info, album_name, encrypted_data, chunk_size=1024)

        cache_key = f"{album_name}/{image_path.name}"
        preview_cache.pop(cache_key, None)
        merge_cache.pop(cache_key, None)

    else:
        with open(IMAGES_META, "r") as read_f:
            old_meta = json.load(read_f)

        albums = old_meta["albums"]
        if album_name not in albums:
            album_id = uuid.uuid4().hex[:32]
            albums[album_name] = {album_id: {}}

        album_id = next(iter(albums[album_name]))
        default_albums = albums[album_name][album_id]

        if image_path.name in default_albums:
            old_entry = default_albums[image_path.name]
            enc_sha256 = hashlib.sha256(encrypted_data).hexdigest()

            if old_entry["sha256"] == enc_sha256:
                QMessageBox.information(None, "PassCore Vault", "Image already exists." )
                return

            else:
                # Modifies existed IMAGES_META json with new entry.
                image_data = {
                    "uuid": image_info["image_id"],
                    "mime": image_info["mime"],
                    "extension": image_path.suffix,
                    "width": image_info["width"],
                    "height": image_info["height"],
                    "size" : len(image_info["image_bytes"]),
                    "sha256": enc_sha256,
                    "created_at": old_entry["created_at"],
                    "modified": timestamp
                }
                old_meta["albums"][album_name][album_id][image_path.name] = image_data
                with open(IMAGES_META, "w") as update_meta:
                    json.dump(old_meta, update_meta, indent=4)

                cache_key = f"{album_name}/{image_path.name}"
                preview_cache.pop(cache_key, None)
                merge_cache.pop(cache_key, None)

                split_image_bin(image_info, album_name, encrypted_data, chunk_size=1024)

                old_id = old_entry["uuid"]
                old_ctn = Path(CONTAINER_DIR / album_id / old_id)
                if old_ctn.exists():
                    secure_del_tree(old_ctn)
        else:
            # Update existed IMAGES_META json with new entries.
            image_data = {
                "uuid": image_info["image_id"],
                "mime": image_info["mime"],
                "extension": image_path.suffix,
                "width": image_info["width"],
                "height": image_info["height"],
                "size" : len(image_info["image_bytes"]),
                "sha256": hashlib.sha256(encrypted_data).hexdigest(),
                "created_at": timestamp,
            }
            old_meta["albums"][album_name][album_id][image_path.name] = image_data
            with open(IMAGES_META, "w") as update_meta:
                json.dump(old_meta, update_meta, indent=4)

            cache_key = f"{album_name}/{image_path.name}"
            preview_cache.pop(cache_key, None)
            merge_cache.pop(cache_key, None)

            split_image_bin(image_info, album_name, encrypted_data, chunk_size=1024)

def decrypt_image(vault_key, encrypted_blobs):
    enc_cipher = AESGCM(vault_key)
    try:
        offset = 0
        while offset < len(encrypted_blobs):
            read_len_data = encrypted_blobs[offset : offset + 4] # Read 4 byte length
            offset += 4
            if not read_len_data:
                break

            length = struct.unpack(">I", read_len_data)[0] # Unpack length integer bytes for first 4 readed lenght at each iteration.
            read_enc_data = encrypted_blobs[offset : offset + length] # Read full byte record.
            offset += length
            nonce, cipher_text = read_enc_data[:12], read_enc_data[12:]
            decrypt_enc_data = enc_cipher.decrypt(nonce, cipher_text, None) # Extract decrypted nonce & cipher text from encryted blobs.
            return decrypt_enc_data

    except InvalidTag:
        return ValueError("Image authentication failed. Wrong key or corrupted image.")

def merge_image_bin(filename, album_name):
    cache_key = f"{album_name}/{filename}"
    if cache_key in merge_cache:
        return merge_cache[cache_key]

    with open(IMAGES_META, "r") as ijson:
        merge_i = json.load(ijson)

    with open(IMAGES_META, "r") as am_d:
        data = json.load(am_d)
    album_id = next(iter(data["albums"][album_name]))
    
    image_ctn = merge_i["albums"][album_name][album_id][filename]["uuid"]
    container_meta = CONTAINER_DIR / album_id / image_ctn / "metadata.json"

    merge_data = bytearray()
    with open(container_meta, "r") as read_meta:
        merge_meta = json.load(read_meta)

    for blob_name, blob_info in merge_meta["blobs"].items():
        container_id = blob_info["container"]
        blob_path = CONTAINER_DIR / album_id / image_ctn / container_id / blob_name

        if not blob_path.exists():
            raise FileNotFoundError(f"Missing blob: {blob_name}")
        
        with open(blob_path, "rb") as f:
            merge_data.extend(f.read())

    merge_hash = hashlib.sha256(merge_data).hexdigest()
    if merge_hash != merge_i["albums"][album_name][album_id][filename]["sha256"]:
        raise FileNotFoundError(f"Merged image: {image_ctn}; failed integrity verification is corrupted.!")

    image_bytes = bytes(merge_data)
    merge_cache[cache_key] = image_bytes
    if len(merge_cache) > MAX_CACHE:
        old = next(iter(merge_cache))
        del merge_cache[old]

    try:
        blob_integrity_verify(filename, album_name)
    except (FileNotFoundError, ValueError) as e:
        return InvalidTag(e)

    return image_bytes

def load_preview(vault_key, filename, album_name):
    cache_key = f"{album_name}/{filename}"
    if cache_key in preview_cache:
        return preview_cache[cache_key]

    encrypted_blobs = merge_image_bin(filename, album_name)
    image_bytes = decrypt_image(vault_key, encrypted_blobs)
    if image_bytes is None:
        return None
    
    buffer = BytesIO(image_bytes)
    img = Image.open(buffer).convert("RGBA")
    out = BytesIO()
    img.save(out, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(out.getvalue())
    preview_cache[cache_key] = pixmap
    if len(preview_cache) > MAX_CACHE: # Delete old cache if exceeds length.!
        old = next(iter(preview_cache))
        del preview_cache[old]

    return pixmap

def blob_integrity_verify(filename, album_name):

    with open(IMAGES_META, "r") as r_meta:
        blob_meta = json.load(r_meta)
    album_id = next(iter(blob_meta["albums"][album_name]))
    
    blob_id = blob_meta["albums"][album_name][album_id][filename]
    blob_meta_path = Path(CONTAINER_DIR / album_id / blob_id["uuid"] / "metadata.json") 
    if not blob_meta_path.exists():
        raise FileNotFoundError("Metadata file is missing")
    
    with open(blob_meta_path, "r") as b_meta:
        ctn_meta = json.load(b_meta)

    expected_blobs = ctn_meta["blobs"] # outputs the blob dict from metadata.
    for blob_name in expected_blobs:
        container_id = expected_blobs[blob_name]["container"]
        blob_path = Path(CONTAINER_DIR / album_id / blob_id["uuid"] / container_id / blob_name) # existing blobs path
        if not blob_path.exists():
            raise FileNotFoundError(f"Missing blob.: {blob_name}")
        
        actual_size = blob_path.stat().st_size # outputs file size of blobs (each blob)
        expected_size = expected_blobs[blob_name]["size"] # Store size of a blob from metadata.
        if actual_size != expected_size: # Compares the physcially stored blob with metadata blobs sizes.!
            raise ValueError(f"blob size mismatch.: {blob_name}")

        expected_hash = expected_blobs[blob_name]["sha256"] # outputs stored hash of existing blob
        actual_hash = sha256_blob(blob_path) # generate hash for existing blob bytes
        if actual_hash != expected_hash:
            raise ValueError(f"Hash mismatch.: {blob_name}")
        
    actual_blobs = len(ctn_meta["blobs"])
    
    if actual_blobs != ctn_meta["blob_count"]:
        raise ValueError("blob count mismatch.!")


def split_image_bin(image_info, album_name, encrypted_data, chunk_size=1024):
    image_id = image_info["image_id"]

    blob_info = {}
    index = 0

    with open(IMAGES_META, "r") as album_ctn:
        data = json.load(album_ctn)
    album_id = next(iter(data["albums"][album_name]))
    
    container_path = CONTAINER_DIR / album_id / image_id
    container_path.mkdir(parents=True, exist_ok=True)

    for offset in range(0, len(encrypted_data), chunk_size):
        chunk = encrypted_data[offset : offset + chunk_size]
        if not chunk:
            return

        blob_container_id = uuid.uuid4().hex[:16]
        blob_container_path = container_path / blob_container_id
        blob_container_path.mkdir(parents=True, exist_ok=True)

        path = (blob_container_path / f"{image_id}_{index:04d}.bin").resolve()
        blob_sha256 = hashlib.sha256(chunk).hexdigest()
        with open(path, "wb") as image_to_path:
            image_to_path.write(chunk)
        
        blob_info[path.name] = {
            "container": blob_container_id,
            "size": (len(chunk)),
            "sha256": blob_sha256
        }
        index += 1

    image_metadata(image_info, album_name, blob_info, encrypted_data)

def image_metadata(image_info, album_name, blob_info, encrypted_data):
    image_id = image_info["image_id"]
    image_path = image_info["image_path"]
    image_bytes = image_info["image_bytes"]

    # CONTAINER_DIR images metadata
    image_entry = {}
    with open(IMAGES_META, "r") as album:
        data = json.load(album)
    album_id = next(iter(data["albums"][album_name]))

    container_meta = CONTAINER_DIR / album_id / image_id / "metadata.json"

    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    image_entry = {
        "uuid": image_id,
        "created_at": timestamp,
        "filename": image_path.name,
        "stem": image_path.stem,
        "extension": image_path.suffix,
        "mime": image_info["mime"],
        "mode": image_info["mode"],
        "format": image_info["format"],
        "width": image_info["width"],
        "height": image_info["height"],
        "size": (len(image_bytes)),
        "encrypted_size": len(encrypted_data),
        "blob_count": len(blob_info),
        "blobs": blob_info
    }
    with open(container_meta, "w") as ijson:
        json.dump(image_entry, ijson, indent=4)

def size_calc(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"
