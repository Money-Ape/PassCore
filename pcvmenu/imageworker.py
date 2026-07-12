from PySide6.QtCore import QObject, Signal, Slot
from pcvmenu.images import load_preview

class ImageLoader(QObject):
    finished = Signal(str, str, object)

    def __init__(self, vault_key):
        super().__init__()
        self.vault_key = vault_key

    @Slot(str, str)
    def load(self, filename, album_name):
        try:
            pix = load_preview(self.vault_key, filename, album_name)

        except Exception as e:
            print(e)
            pix = None

        self.finished.emit(album_name, filename, pix)
        