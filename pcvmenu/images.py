from PIL import Image
import sys, os, platform, mimetypes, uuid
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
        self.image_path = Path(image_file)

        if not self.image_path:
            return

        with Image.open(self.image_path) as PCi:
            print("==============IMAGE==============")
            print("Name      :    ",self.image_path.name)
            print("Stem      :    ",self.image_path.stem)
            print("Suffix    :    ",self.image_path.suffix)
            print("Format    :    ",PCi.format)
            print("Width     :    ",PCi.width)
            print("Height    :    ",PCi.height)
            print("Mode      :    ",PCi.mode)

        with open(self.image_path, "rb") as img:
            img_bytes = img.read()
            print(f"Binary Size :  {len(img_bytes)} bytes")
        
        mime, _ = mimetypes.guess_type(self.image_path)
        print("mime type : ", mime)

        object_id = uuid.uuid5().hex[:32]
        print(f"UUID[{len(object_id)}] : {object_id}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassCoreImage()
    window.show()

    sys.exit(app.exec())