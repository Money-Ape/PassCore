from PIL import Image
import sys, os, platform, mimetypes, uuid, hashlib, json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap
from datetime import datetime
from io import BytesIO

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

class PassCoreImage(QMainWindow):
    def __init__(self):
        super().__init__()
    
    @staticmethod
    def import_image(image_path, album_name):
        image_path = Path(image_path)
        with Image.open(image_path) as PCi:

            with open(image_path, "rb") as img:
                image_bytes = img.read()

            mime, _ = mimetypes.guess_type(image_path)

            # PASSCORE_DIR images metadata
            image_info = {
                "object_id": uuid.uuid4().hex[:32],
                "image_path": image_path,
                "image_bytes": image_bytes,
                "mime": mime,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "sha256": hashlib.sha256(image_bytes).hexdigest()
            }
        PassCoreImage.split_image_bin(image_info, album_name)

        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        # PASSCORE_DIR images metadata
        image_meta = {
            "albums": {
                "Default": {
                    image_path.name: {
                        "uuid": image_info["object_id"],
                        "mime": mime,
                        "extension": image_path.suffix,
                        "sha256": image_info["sha256"],
                        "created_at": timestamp,
                    }
                }
            }
        }
        if not IMAGES_META.exists(): # Initially create if IMAGES_META json not exists
            with open(IMAGES_META, "w") as f_init:
                json.dump(image_meta, f_init, indent=4)

            PassCoreImage.split_image_bin(image_info, album_name, chunk_size=1024)

        else:
            with open(IMAGES_META, "r", encoding="utf-8") as read_f:
                old_meta = json.load(read_f)
            
            albums = old_meta["albums"]
            if "Default" not in albums:
                albums[album_name] = {}
            
            default_albums = albums[album_name]
            
            if image_path.name in default_albums:
                old_entry = default_albums[image_path.name]
                if old_entry["sha256"] == image_info["sha256"]:
                    QMessageBox.information(None, "PassCore Vault", "Image already exists." )
                    PassCoreImage.blob_integrity_verify(image_info, album_name)
                    PassCoreImage.merge_image_bin(image_path.name, album_name)
                    return

                else:
                    # Modifies existed IMAGES_META json with new entry.
                    image_data = {
                        "uuid": image_info["object_id"],
                        "width": image_info["width"],
                        "height": image_info["height"],
                        "size" : len(image_info["image_bytes"]),
                        "sha256": image_info["sha256"],
                        "created_at": old_entry["created_at"],
                        "modified": timestamp
                    }
                    default_albums[image_path.name] = image_data
                    with open(IMAGES_META, "w", encoding="utf-8") as update_meta:
                        json.dump(default_albums, update_meta, indent=4)
                    
                    PassCoreImage.split_image_bin(image_info, album_name, chunk_size=1024)
                    
                    old_id = old_entry["uuid"]
                    old_ctn = Path(CONTAINER_DIR / old_id)
                    if old_ctn.exists():
                        secure_del_tree(old_ctn)
            else:
                # Update existed IMAGES_META json with new entries.
                image_data = {
                    "uuid": image_info["object_id"],
                    "width": image_info["width"],
                    "height": image_info["height"],
                    "size" : len(image_info["image_bytes"]),
                    "sha256": image_info["sha256"],
                    "created_at": timestamp,
                }
                default_albums[image_path.name] = image_info
                with open(IMAGES_META, "w", encoding="utf-8") as update_meta:
                    json.dump(old_meta, update_meta, indent=4)

                PassCoreImage.split_image_bin(image_info, album_name, chunk_size=1024)

    @staticmethod
    def merge_image_bin(filename, album_name):
        with open(IMAGES_META, "r") as ijson:
            merge_i = json.load(ijson)
        
        image_id = merge_i["albums"][album_name][filename]["uuid"]
        container_meta = CONTAINER_DIR / image_id / "metadata.json"

        merge_data = bytearray()
        with open(container_meta, "r", encoding="utf-8") as read_meta:
            merge_meta = json.load(read_meta)

        for blob_name, blob_info in merge_meta["blobs"].items():
            container_id = blob_info["container"]
            blob_path = CONTAINER_DIR / image_id / container_id / blob_name

            if not blob_path.exists():
                raise FileNotFoundError(f"Missing blob: {blob_name}")
            
            with open(blob_path, "rb") as f:
                merge_data.extend(f.read())

        merge_hash = hashlib.sha256(merge_data).hexdigest()
        if merge_hash != merge_i["albums"][album_name][filename]["sha256"]:
            raise FileNotFoundError(f"Merged image: {image_id}; failed integrity verification is corrupted.!")

        return bytes(merge_data)

    @staticmethod
    def load_preview(filename, album_name):
        image_bytes = PassCoreImage.merge_image_bin(filename, album_name)
        if image_bytes is None:
            return None
        
        buffer = BytesIO(image_bytes)
        img = Image.open(buffer).convert("RGBA")
        out = BytesIO()
        img.save(out, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(out.getvalue())
        return pixmap

    def blob_integrity_verify(image_info, album_name):
        image_path = image_info["image_path"]

        with open(IMAGES_META, "r") as r_meta:
            blob_meta = json.load(r_meta)
        
        blob_id = blob_meta["albums"][album_name][image_path.name]
        blob_meta_path = Path(CONTAINER_DIR / blob_id["uuid"] / "metadata.json") 
        if not blob_meta_path.exists():
            raise FileNotFoundError("Metadata file is missing")
        
        with open(blob_meta_path, "r", encoding="utf-8") as b_meta:
            ctn_meta = json.load(b_meta)

        expected_blobs = ctn_meta["blobs"] # outputs the blob dict from metadata.
        for blob_name in expected_blobs:
            container_id = expected_blobs[blob_name]["container"]
            blob_path = Path(CONTAINER_DIR / blob_id["uuid"] / container_id / blob_name) # existing blobs path
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

    @staticmethod
    def split_image_bin(image_info, album_name, chunk_size=1024):
        object_id = image_info["object_id"]
        image_path = image_info["image_path"]
        image_bytes = image_info["image_bytes"]

        blob_info = {}
        index = 0
        
        container_path = CONTAINER_DIR / object_id
        container_path.mkdir(parents=True, exist_ok=True)

        for offset in range(0, len(image_bytes), chunk_size):
            chunk = image_bytes[offset : offset + chunk_size]
            if not chunk:
                return

            blob_container_id = uuid.uuid4().hex[:16]
            blob_container_path = container_path / blob_container_id
            blob_container_path.mkdir(parents=True, exist_ok=True)

            path = (blob_container_path / f"{object_id}_{index:04d}.bin").resolve()
            blob_sha256 = hashlib.sha256(chunk).hexdigest()
            with open(path, "wb") as image_to_path:
                image_to_path.write(chunk)
            
            blob_info[path.name] = {
                "container": blob_container_id,
                "size": (len(chunk)),
                "sha256": blob_sha256
            }
            index += 1

        PassCoreImage.image_metadata(image_info, blob_info, album_name)

    @staticmethod
    def image_metadata(image_info, blob_info, album_name):
        object_id = image_info["object_id"]
        image_path = image_info["image_path"]
        image_bytes = image_info["image_bytes"]

        # CONTAINER_DIR images metadata
        image_entry = {}
        container_meta = CONTAINER_DIR / object_id / "metadata.json"

        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        image_entry = {
            "uuid": object_id,
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
            "blob_count": len(blob_info),
            "blobs": blob_info
        }
        with open(container_meta, "w") as ijson:
            json.dump(image_entry, ijson, indent=4)

        PassCoreImage.blob_integrity_verify(image_info, album_name)

    def size_calc(self, size):
        units = ["Bytes", "KB", "MB", "GB", "TB"]
        for unit in units:
            if size < 1024 or unit == "TB":
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassCoreImage()
    window.show()

    sys.exit(app.exec())