from PIL import Image
import sys, os, platform, mimetypes, uuid, hashlib, json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
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
        return Path.home() / ".local" / "share" / ".passcore_db"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData"
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
        image = Path.home() / "Pictures"

        image_file, _ = QFileDialog.getOpenFileName(
            self, "Select image", str(image), "", "PNG Images (*.png)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not image_file:
            return

        self.image_path = Path(image_file)
        with Image.open(self.image_path) as self.PCi:

            with open(self.image_path, "rb") as img:
                self.image_bytes = img.read()
            
                self.mime, _ = mimetypes.guess_type(self.image_path)
                self.object_id = uuid.uuid4().hex[:32]
                self.sha256 = hashlib.sha256(self.image_bytes).hexdigest()

        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

        # PASSCORE_DIR images metadata
        self.image_meta = {
            "file": {
                self.image_path.name: {
                    "uuid": self.object_id,
                    "mime": self.mime,
                    "extension": self.image_path.suffix,
                    "sha256": self.sha256,
                    "created_at": timestamp,
                }
            }
        }
        if not IMAGES_META.exists(): # Initially create if IMAGES_META json not exists
            with open(IMAGES_META, "w") as f_init:
                json.dump(self.image_meta, f_init, indent=4)
            
            self.split_image_bin(self.image_bytes, chunk_size=1024)

        else:
            with open(IMAGES_META, "r", encoding="utf-8") as read_f:
                old_meta = json.load(read_f)
            
            if self.image_path.name in old_meta["file"]:
                old_entry = old_meta["file"][self.image_path.name]
                if old_entry["sha256"] == self.sha256:
                    QMessageBox.information(self, "PassCore Vault", "Image already exists." )
                    self.blob_integrity_verify()
                    self.merge_image_bin()
                    return

                else:
                    # Modifies existed IMAGES_META json with new entry.
                    image_info = {
                        "uuid": self.object_id,
                        "mime": self.mime,
                        "extension": self.image_path.suffix,
                        "sha256": self.sha256,
                        "created_at": old_entry["created_at"],
                        "modified": timestamp
                    }
                    old_meta["file"][self.image_path.name] = image_info
                    with open(IMAGES_META, "w", encoding="utf-8") as update_meta:
                        json.dump(old_meta, update_meta, indent=4)
                    
                    self.split_image_bin(self.image_bytes, chunk_size=1024)
                    
                    old_id = old_entry["uuid"]
                    old_ctn = Path(CONTAINER_DIR / "images" / old_id)
                    if old_ctn.exists():
                        secure_del_tree(old_ctn)
            else:
                # Update existed IMAGES_META json with new entries.
                image_info = {
                    "uuid": self.object_id,
                    "mime": self.mime,
                    "extension": self.image_path.suffix,
                    "sha256": self.sha256,
                    "created_at": timestamp,
                }
                old_meta["file"][self.image_path.name] = image_info
                with open(IMAGES_META, "w", encoding="utf-8") as update_meta:
                    json.dump(old_meta, update_meta, indent=4)

                self.split_image_bin(self.image_bytes, chunk_size=1024)

    def merge_image_bin(self):
        with open(IMAGES_META, "r") as ijson:
            merge_i = json.load(ijson)
        
        image_id = merge_i["file"][self.image_path.name]["uuid"]
        container_meta = CONTAINER_DIR / "images" / image_id / "metadata.json"

        merge_data = bytearray()
        with open(container_meta, "r", encoding="utf-8") as read_meta:
            merge_meta = json.load(read_meta)

        for blob_name, blob_info in merge_meta["blobs"].items():
            container_id = blob_info["container"]
            blob_path = CONTAINER_DIR / "images" / image_id / container_id / blob_name

            if not blob_path.exists():
                raise FileNotFoundError(f"Missing blob: {blob_name}")
            
            with open(blob_path, "rb") as f:
                merge_data.extend(f.read())

        merge_hash = hashlib.sha256(merge_data).hexdigest()
        if merge_hash != merge_i["file"][self.image_path.name]["sha256"]:
            raise FileNotFoundError(f"{image_id} is corrupted.!")

        buffer = BytesIO(merge_data)
        buffer_i = Image.open(buffer)
        buffer_i.show()

    def blob_integrity_verify(self):
        with open(IMAGES_META, "r") as r_meta:
            blob_meta = json.load(r_meta)
        
        blob_id = blob_meta["file"][self.image_path.name]
        blob_meta_path = Path(CONTAINER_DIR / "images" / blob_id["uuid"] / "metadata.json") 
        if not blob_meta_path.exists():
            raise FileNotFoundError("Metadata file is missing")
        
        with open(blob_meta_path, "r", encoding="utf-8") as b_meta:
            ctn_meta = json.load(b_meta)

        expected_blobs = ctn_meta["blobs"] # outputs the blob dict from metadata.
        for blob_name in expected_blobs:
            container_id = expected_blobs[blob_name]["container"]
            blob_path = Path(CONTAINER_DIR / "images" / blob_id["uuid"] / container_id / blob_name) # existing blobs path
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

    def split_image_bin(self, image_bytes, chunk_size=1024):
        self.blob_info = {}
        index = 0
        
        container_path = CONTAINER_DIR / "images" / self.object_id
        container_path.mkdir(parents=True, exist_ok=True)

        for offset in range(0, len(image_bytes), chunk_size):
            chunk = image_bytes[offset : offset + chunk_size]
            if not chunk:
                return

            blob_container_id = uuid.uuid4().hex[:16]
            blob_container_path = container_path / blob_container_id
            blob_container_path.mkdir(parents=True, exist_ok=True)

            path = (blob_container_path / f"{self.object_id}_{index:04d}.bin").resolve()
            blob_sha256 = hashlib.sha256(chunk).hexdigest()
            with open(path, "wb") as image_to_path:
                image_to_path.write(chunk)
            
            self.blob_info[path.name] = {
                "container": blob_container_id,
                "size": (len(chunk)),
                "sha256": blob_sha256
            }
            index += 1

        self.image_metadata()

    def image_metadata(self):

        # CONTAINER_DIR images metadata
        image_entry = {}
        container_meta = CONTAINER_DIR / "images" / self.object_id / "metadata.json"

        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        image_entry = {
            "uuid": self.object_id,
            "created_at": timestamp,
            "filename": self.image_path.name,
            "stem": self.image_path.stem,
            "extension": self.image_path.suffix,
            "mime": self.mime,
            "mode": self.PCi.mode,
            "format": self.PCi.format,
            "width": self.PCi.width,
            "height": self.PCi.height,
            "size": (len(self.image_bytes)),
            "blob_count": len(self.blob_info),
            "blobs": self.blob_info
        }
        with open(container_meta, "w") as ijson:
            json.dump(image_entry, ijson, indent=4)

        self.blob_integrity_verify()
        self.merge_image_bin()

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