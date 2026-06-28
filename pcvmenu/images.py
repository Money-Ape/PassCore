from PIL import Image
import sys, os, platform, mimetypes, uuid, hashlib
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog

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

        with Image.open(self.image_path) as PCi:

            with open(self.image_path, "rb") as img:
                self.image_bytes = img.read()
            
                mime, _ = mimetypes.guess_type(self.image_path)
                object_id = uuid.uuid4().hex[:32]
                sha256 = hashlib.sha256(self.image_bytes).hexdigest()
                self.image_entry = {
                    "uuid": object_id,
                    "type": mime,
                    "filename": self.image_path.stem,
                    "extension": self.image_path.suffix,
                    "mode": PCi.mode,
                    "size": self.size_calc(len(self.image_bytes)),
                    "width": PCi.width,
                    "height": PCi.height,
                    "sha256": sha256
                }
                for key, value in self.image_entry.items():
                    print(f"{key:<10} : {value}")
    
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