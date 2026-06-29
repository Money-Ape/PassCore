from PIL import Image
import sys, os, platform, mimetypes, uuid, hashlib, json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from datetime import datetime
from io import BytesIO

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

                self.split_image_bin(self.image_bytes, chunk_size=1024)

    def merge_image_bin(self):
        with open(self.container_meta, "r", encoding="utf-8") as read_meta:
            image_meta = json.load(read_meta)

        merge_data = bytearray()
        meta_uuid = image_meta["uuid"]
        for blob_name, blob_info in image_meta["blobs"].items():
            container_id = blob_info["container"]
            blob_path = CONTAINER_DIR / "images" / meta_uuid / container_id / blob_name

            if not blob_path.exists():
                raise FileNotFoundError(f"Missing blob: {blob_name}")
            
            with open(blob_path, "rb") as f:
                merge_data.extend(f.read())
            
        buffer = BytesIO(merge_data)
        buffer_i = Image.open(buffer)
        buffer_i.show()

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
        image_entry = {}
        self.container_meta = CONTAINER_DIR / "images" / self.object_id / "metadata.json"

        timestamp = datetime.now().strftime("%d-%M-%Y %I:%M:%S %p")
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
            "sha256": self.sha256,
            "blob_count": len(self.blob_info),
            "blobs": self.blob_info
        }
        with open(self.container_meta, "w") as ijson:
            json.dump(image_entry, ijson, indent=4)

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