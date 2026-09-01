import io, json, os, struct, zipfile
from datetime import datetime
from pathlib import Path
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QLineEdit, QAbstractItemView, QCheckBox)
from security.yaml_secure import secure_load, convert_yaml_to_text, VaultValidationError
from pcvmenu.images import IMAGES_META, merge_image_bin, decrypt_image, import_image_bytes

PACKAGE_MAGIC = b"PASSCORE-PCX\x01"
PACKAGE_VERSION = 2  # v2 adds an explicit protected-flag byte; v1 (always protected) still reads fine.
KDF_TIME = 3
KDF_MEMORY = 65536
KDF_PARALLELISM = 4
KDF_LENGTH = 32

def _derive_package_key(password: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=KDF_TIME,
        memory_cost=KDF_MEMORY,
        parallelism=KDF_PARALLELISM,
        hash_len=KDF_LENGTH,
        type=Type.ID,
    )

def _encrypt_package(payload: bytes, password: str | None) -> bytes:
    protected = bool(password)
    header = (PACKAGE_MAGIC + struct.pack(">B", PACKAGE_VERSION) + struct.pack(">B", 1 if protected else 0))

    if not protected:
        return header + payload

    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_package_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, payload, PACKAGE_MAGIC)

    return header + salt + nonce + ciphertext

def _decrypt_package(package: bytes, password: str | None) -> bytes:
    if len(package) < len(PACKAGE_MAGIC) + 1:
        raise ValueError("Invalid or incomplete PassCore package.")

    if not package.startswith(PACKAGE_MAGIC):
        raise ValueError("This file is not a valid PassCore package.")

    offset = len(PACKAGE_MAGIC)
    version = package[offset]
    offset += 1

    if version == 1:
        protected = True  # Legacy packages predate the protected-flag byte and were always encrypted.

    elif version == 2:
        if len(package) < offset + 1:
            raise ValueError("Invalid or incomplete PassCore package.")

        protected = bool(package[offset])
        offset += 1

    else:
        raise ValueError(f"Unsupported PassCore package version: {version}")

    if not protected:
        return package[offset:]

    minimum_remaining = 16 + 12 + 16  # salt + nonce + AESGCM tag
    if len(package) < offset + minimum_remaining:
        raise ValueError("Invalid or incomplete PassCore package.")

    salt = package[offset:offset + 16]
    offset += 16

    nonce = package[offset:offset + 12]
    offset += 12

    ciphertext = package[offset:]

    if not password:
        raise ValueError("This package is password protected.\n\nEnter the package password to import it.")

    key = _derive_package_key(password, salt)

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, PACKAGE_MAGIC)

    except InvalidTag:
        raise ValueError("Wrong package password or corrupted package.")

def _build_inner_zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,) as archive:
        for name, data in files.items():
            archive.writestr(name, data)

    return buffer.getvalue()

def _read_inner_zip(data: bytes) -> dict[str, bytes]:
    result = {}

    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue

            result[info.filename] = archive.read(info.filename)

    return result

def _safe_filename(name: str) -> str:
    return Path(name).name.replace("/", "_").replace("\\", "_")

class ImportExportWizard(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent_window = parent
        self.setWindowTitle("PassCore — Import / Export")
        self.setMinimumSize(620, 560)
        self.resize(680, 600)

        self._build_ui()
        self._refresh_import_ui()
        self._refresh_export_list()

    def _build_ui(self):    # ========================================================== UI
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.import_tab = QWidget()
        self.export_tab = QWidget()

        self.tabs.addTab(self.import_tab, "Import")
        self.tabs.addTab(self.export_tab, "Export")

        self._build_import_tab()
        self._build_export_tab()

        layout.addWidget(self.tabs)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _build_import_tab(self):
        layout = QVBoxLayout(self.import_tab)

        intro = QLabel(
            "Import PassCore data into the currently unlocked vault.\n"
            "Imports are type-checked before anything is written."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Import as:"))

        self.import_type = QComboBox()
        self.import_type.addItem("Credentials", "credentials")
        self.import_type.addItem("Images", "images")
        self.import_type.currentIndexChanged.connect(self._refresh_import_ui)

        type_row.addWidget(self.import_type, 1)
        layout.addLayout(type_row)

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Source:"))

        self.import_source = QComboBox()
        self.import_source.currentIndexChanged.connect(self._update_import_source_ui)

        source_row.addWidget(self.import_source, 1)
        layout.addLayout(source_row)

        self.import_info = QLabel()
        self.import_info.setWordWrap(True)
        layout.addWidget(self.import_info)

        self.import_file = QLineEdit()
        self.import_file.setReadOnly(True)
        self.import_file.setPlaceholderText("No package selected")

        file_row = QHBoxLayout()
        file_row.addWidget(self.import_file, 1)

        self.import_browse = QPushButton("Browse…")
        self.import_browse.clicked.connect(self._browse_import)

        file_row.addWidget(self.import_browse)
        layout.addLayout(file_row)

        self.import_password = QLineEdit()
        self.import_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.import_password.setPlaceholderText("Package password (leave blank if not password protected)")

        self.import_password_label = QLabel("Package Password (optional):")
        self.import_show_password = QCheckBox("Show Password")
        self.import_show_password.toggled.connect(self._toggle_import_password)

        layout.addWidget(self.import_password_label)
        layout.addWidget(self.import_password)
        layout.addWidget(self.import_show_password)

        self.import_text_btn = QPushButton("Import Text")
        self.import_package_btn = QPushButton("Import Vault Package")

        self.import_text_btn.clicked.connect(self._import_text)
        self.import_package_btn.clicked.connect(self._import_package)

        self.import_action_row = QHBoxLayout()
        self.import_action_row.addWidget(self.import_text_btn)
        self.import_action_row.addWidget(self.import_package_btn)

        layout.addLayout(self.import_action_row)
        layout.addStretch()

    def _toggle_import_password(self, checked):
        mode = (
            QLineEdit.EchoMode.Normal
            if checked
            else QLineEdit.EchoMode.Password
        )
        self.import_password.setEchoMode(mode)

    def _build_export_tab(self):
        layout = QVBoxLayout(self.export_tab)

        intro = QLabel(
            "Choose what you want to export. Multiple credentials or "
            "multiple image albums can be selected."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Export:"))

        self.export_type = QComboBox()
        self.export_type.addItem("Credentials", "credentials")
        self.export_type.addItem("Images", "images")
        self.export_type.currentIndexChanged.connect(self._refresh_export_list)

        type_row.addWidget(self.export_type, 1)
        layout.addLayout(type_row)

        self.select_all_btn = QPushButton("Select All")
        self.clear_all_btn = QPushButton("Clear All")

        self.select_all_btn.clicked.connect(lambda: self._set_all_export_items(True))
        self.clear_all_btn.clicked.connect(lambda: self._set_all_export_items(False))

        selection_buttons = QHBoxLayout()
        selection_buttons.addWidget(self.select_all_btn)
        selection_buttons.addWidget(self.clear_all_btn)
        selection_buttons.addStretch()

        layout.addLayout(selection_buttons)

        self.export_list = QListWidget()
        self.export_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.export_list, 1)

        self.export_count = QLabel("0 selected")
        layout.addWidget(self.export_count)

        self.export_protect = QCheckBox("Password protect this export")
        self.export_protect.setChecked(False)
        self.export_protect.toggled.connect(self._toggle_export_protect)
        layout.addWidget(self.export_protect)

        self.export_password_label = QLabel("Package Password:")
        self.export_password = QLineEdit()
        self.export_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.export_password.setPlaceholderText("Choose a package password")

        layout.addWidget(self.export_password_label)
        layout.addWidget(self.export_password)

        self._toggle_export_protect(False)  # Start hidden/disabled to match the unchecked default.

        self.export_btn = QPushButton("Export Selected")
        self.export_btn.clicked.connect(self._export_selected)
        layout.addWidget(self.export_btn)

    def _toggle_export_protect(self, checked):
        self.export_password_label.setVisible(checked)
        self.export_password.setVisible(checked)
        if not checked:
            self.export_password.clear()

    def _refresh_import_ui(self):
        object_type = self.import_type.currentData()
        self.import_source.blockSignals(True)
        self.import_source.clear()

        if object_type == "credentials":
            self.import_source.addItem(
                "Import Text",
                "text"
            )
            self.import_source.addItem(
                "Import PassCore Package",
                "package"
            )
            self.import_info.setText(
                "Credentials accepts text files or a Credentials "
                "package. An Images package will be rejected."
            )

        elif object_type == "images":
            self.import_source.addItem(
                "Import PassCore Package",
                "package"
            )
            self.import_info.setText(
                "Images accepts an Images package containing one "
                "or more albums. Credential packages are rejected."
            )

        self.import_source.blockSignals(False)
        self._update_import_source_ui()
        self.import_file.clear()

    def _update_import_source_ui(self):
        source = self.import_source.currentData()

        is_text = source == "text"
        is_package = source == "package"

        self.import_text_btn.setVisible(is_text)
        self.import_package_btn.setVisible(is_package)
        self.import_password_label.setVisible(is_package)
        self.import_password.setVisible(is_package)
        self.import_show_password.setVisible(is_package)

        self.import_file.clear()

    def _refresh_export_list(self):
        self.export_list.clear()

        object_type = self.export_type.currentData()
        if object_type == "credentials":
            for index, note in enumerate(getattr(self.parent_window, "notes", [])):
                title = str(note.get("title") or "Untitled Note")

                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, index)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.export_list.addItem(item)

        else:
            if IMAGES_META.exists():
                try:
                    with open(IMAGES_META, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    for album_name in sorted(data.get("albums", {})):
                        item = QListWidgetItem(album_name)
                        item.setData(Qt.ItemDataRole.UserRole, album_name)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        self.export_list.addItem(item)

                except (OSError, json.JSONDecodeError) as e:
                    QMessageBox.warning(
                        self,
                        "PassCore", f"Unable to read image metadata.\n\n{e}",
                    )

        self.export_list.itemChanged.connect(self._update_export_count)
        self._update_export_count()

    def _update_export_count(self, *_):
        count = 0

        for i in range(self.export_list.count()):
            item = self.export_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                count += 1

        self.export_count.setText(f"{count} selected")

    def _set_all_export_items(self, checked):
        state = (
            Qt.CheckState.Checked
            if checked
            else Qt.CheckState.Unchecked
        )
        self.export_list.blockSignals(True)

        for i in range(self.export_list.count()):
            self.export_list.item(i).setCheckState(state)

        self.export_list.blockSignals(False)
        self._update_export_count()

    def _browse_import(self):   # ========================================================== File selection
        source = self.import_source.currentData()

        if source == "text":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Text",
                str(Path.home()),
                "Text Files (*.txt);;All Files (*)",
                options=QFileDialog.Option.DontUseNativeDialog,
            )

        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Import PassCore Package",
                str(Path.home()),
                "PassCore Package (*.pcx);;All Files (*)",
                options=QFileDialog.Option.DontUseNativeDialog,
            )

        if path:
            self.import_file.setText(path)

    def _import_text(self): # ========================================================== Import
        path = self.import_file.text().strip()

        if not path:
            QMessageBox.information(self, "PassCore", "Select a text file first.")
            return

        from file import import_txt # Reuse the existing secure text importer.

        try:
            with open(path, "r", encoding="utf-8") as f:
                imported = f.read()

            try:
                parsed = secure_load(imported)
                imported = convert_yaml_to_text(parsed)

            except VaultValidationError as e:
                QMessageBox.critical(self, "Invalid YAML", str(e))
                return

            except Exception:
                pass # Preserve existing behaviour: ordinary text remains text.

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))
            return

        if self.parent_window.key is None:
            QMessageBox.information(self, "PassCore", "Unlock the vault before importing.")
            return

        title = Path(path).stem or "Imported Note" # Import Text is intentionally credentials-only.
        self.parent_window.notes.append({
            "title": title,
            "content": imported,
        })
        self.parent_window.show_credentials()

        if hasattr(self.parent_window, "utility"):
            self.parent_window.utility.mark_vault_changed()

        self.parent_window.save_btn.click() # The real save slot is connected by enc.py.

        QMessageBox.information(self, "PassCore", f"'{title}' imported successfully.")
        self.accept()

    def _import_package(self):
        if self.parent_window.key is None:
            QMessageBox.information(self, "PassCore", "Unlock the vault before importing.")
            return

        path = self.import_file.text().strip()
        password = self.import_password.text() or None

        if not path:
            QMessageBox.information(self, "PassCore", "Select a PassCore package first.")
            return

        try:
            with open(path, "rb") as f:
                package = f.read()

            inner = _read_inner_zip(_decrypt_package(package, password))

            if "manifest.json" not in inner:
                raise ValueError("Package manifest is missing.")

            manifest = json.loads(inner["manifest.json"].decode("utf-8"))

            package_type = manifest.get("type")
            selected_type = self.import_type.currentData()

            if package_type != selected_type:
                raise ValueError(
                    "Import type mismatch.\n\n"
                    f"Package: {package_type}\n"
                    f"Selected: {selected_type}\n\n"
                    "This package cannot be imported into "
                    "the selected section."
                )

            if package_type == "credentials":
                self._import_credentials_package(manifest, inner)

            elif package_type == "images":
                self._import_images_package(manifest, inner)

            else:
                raise ValueError(f"Unsupported package type: {package_type}")

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def _import_credentials_package(self, manifest, files):
        imported = []

        for entry in manifest.get("items", []):
            filename = entry["file"]

            if filename not in files:
                raise ValueError(f"Missing note payload: {filename}")

            note = json.loads(files[filename].decode("utf-8"))

            title = str(note.get("title") or "Imported Note")
            content = str(note.get("content") or "")
            title = self._unique_note_title(title) # Avoid silently overwriting an existing note.

            imported.append({
                "title": title,
                "content": content,
            })

        if not imported:
            raise ValueError(
                "The package contains no credential notes."
            )

        self.parent_window.notes.extend(imported)
        self.parent_window.show_credentials()

        if hasattr(self.parent_window, "utility"):
            self.parent_window.utility.mark_vault_changed()

        self.parent_window.save_btn.click() # enc.py owns the actual encryption/save pipeline.

        QMessageBox.information(self, "PassCore", f"Imported {len(imported)} note(s) successfully.")
        self.accept()

    def _import_images_package(self, manifest, files):
        imported_images = 0
        imported_albums = 0

        for album in manifest.get("albums", []):
            album_name = album["name"]

            if not album_name.strip():
                continue

            album_name = self._unique_album_name(album_name) # Avoid silently merging into an existing album.

            imported_albums += 1
            for image in album.get("images", []):
                filename = _safe_filename(
                    image["filename"]
                )
                payload_name = image["file"]

                if payload_name not in files:
                    raise ValueError(
                        f"Missing image payload: {payload_name}"
                    )

                filename = self._unique_image_filename(album_name, filename) # Defensive: avoid in-package filename collisions too.

                image_bytes = files[payload_name]
                import_image_bytes(
                    filename=filename,
                    image_bytes=image_bytes,
                    album_name=album_name,
                    vault_key=self.parent_window.key,
                )
                imported_images += 1

        if imported_images == 0:
            raise ValueError(
                "The package contains no images."
            )

        if hasattr(self.parent_window, "utility"):
            self.parent_window.utility.mark_vault_changed()

        self.parent_window.show_images()
        QMessageBox.information(
            self,
            "PassCore",
            f"Imported {imported_images} image(s) "
            f"from {imported_albums} album(s).",
        )
        self.accept()

    def _checked_export_items(self): # ========================================================== Export
        result = []

        for i in range(self.export_list.count()):
            item = self.export_list.item(i)

            if item.checkState() == Qt.CheckState.Checked:
                result.append(
                    item.data(Qt.ItemDataRole.UserRole)
                )

        return result

    def _export_selected(self):
        if self.parent_window.key is None:
            QMessageBox.information(self, "PassCore", "Unlock the vault before exporting.")
            return

        selected = self._checked_export_items()

        if not selected:
            QMessageBox.information(
                self,
                "PassCore",
                "Select at least one item.",
            )
            return

        password = None
        if self.export_protect.isChecked():
            password = self.export_password.text()

            if not password:
                QMessageBox.warning(self, "PassCore", "Choose a package password, or uncheck 'Password protect this export'.")
                return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PassCore Package",
            "PassCore_export.pcx",
            "PassCore Package (*.pcx)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not path:
            return

        if not path.lower().endswith(".pcx"):
            path += ".pcx"

        try:
            object_type = self.export_type.currentData()

            if object_type == "credentials":
                inner = self._build_credentials_export(selected)

            else:
                inner = self._build_images_export(selected)

            package = _encrypt_package(_build_inner_zip(inner), password)
            with open(path, "wb") as f:
                f.write(package)

            QMessageBox.information(
                self,
                "PassCore",
                "Export completed successfully.\n\n"
                f"{path}",
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _build_credentials_export(self, selected):
        files = {}

        manifest = {
            "format": "PassCore Object Package",
            "version": 1,
            "type": "credentials",
            "created": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
            "items": [],
        }

        notes = getattr(self.parent_window, "notes", [])

        for output_index, note_index in enumerate(selected):
            if note_index < 0 or note_index >= len(notes):
                continue

            note = notes[note_index]
            payload = {
                "title": str(
                    note.get("title") or "Untitled Note"
                ),
                "content": str(
                    note.get("content") or ""
                ),
                "exported_at": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            }

            filename = f"notes/{output_index:04d}.json"

            files[filename] = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            manifest["items"].append({
                "file": filename,
                "title": payload["title"],
            })

        if not manifest["items"]:
            raise ValueError(
                "No valid notes were selected."
            )

        files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        return files

    def _build_images_export(self, selected):
        if not IMAGES_META.exists():
            raise ValueError("Image metadata does not exist.")

        with open(IMAGES_META, "r", encoding="utf-8") as f:
            data = json.load(f)

        files = {}
        manifest = {
            "format": "PassCore Object Package",
            "version": 1,
            "type": "images",
            "created": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
            "albums": [],
        }
        for album_name in selected:
            albums = data.get("albums", {})

            if album_name not in albums:
                continue

            album_id = next(iter(albums[album_name]))
            album_data = albums[album_name][album_id]
            album_entry = {
                "name": album_name,
                "exported_at": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
                "images": [],
            }
            for image_index, (filename, info, ) in enumerate(album_data.items()):
                encrypted = merge_image_bin(filename, album_name)
                image_bytes = decrypt_image(self.parent_window.key, encrypted)

                if isinstance(image_bytes, ValueError):
                    raise image_bytes

                safe_name = _safe_filename(filename)

                payload_name = (
                    f"images/{len(manifest['albums']):04d}/"
                    f"{image_index:04d}_{safe_name}"
                )
                files[payload_name] = image_bytes

                album_entry["images"].append({
                    "filename": safe_name,
                    "file": payload_name,
                    "extension": info.get("extension", Path(filename).suffix),
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "mime": info.get("mime")
                })

            manifest["albums"].append(
                album_entry
            )

        if not manifest["albums"]:
            raise ValueError("No valid image albums were selected.")

        files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        return files

    def _unique_album_name(self, album_name): # ========================================================== Helpers
        """Avoid silently merging an imported album into an existing one
        with the same name - create a new album (name (1), (2), ...)
        instead, matching how note titles are de-duplicated on import."""
        existing = set()

        if IMAGES_META.exists():
            with open(IMAGES_META, "r", encoding="utf-8") as f:
                data = json.load(f)

            existing = set(data.get("albums", {}).keys())

        if album_name not in existing:
            return album_name

        counter = 1
        while f"{album_name} ({counter})" in existing:
            counter += 1

        return f"{album_name} ({counter})"

    def _unique_image_filename(self, album_name, filename): # ========================================================== Helpers
        existing = set()

        if IMAGES_META.exists():
            with open(IMAGES_META, "r", encoding="utf-8") as f:
                data = json.load(f)

            albums = data.get("albums", {})
            if album_name in albums and albums[album_name]:
                album_id = next(iter(albums[album_name]))
                existing = set(albums[album_name][album_id].keys())

        if filename not in existing:
            return filename

        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1

        while f"{stem} ({counter}){suffix}" in existing:
            counter += 1

        return f"{stem} ({counter}){suffix}"

    def _unique_note_title(self, title): # ========================================================== Helpers
        existing = {
            str(note.get("title", "")).strip()
            for note in getattr(
                self.parent_window, "notes", []
            )
        }

        if title not in existing:
            return title

        base = title
        counter = 1

        while f"{base} ({counter})" in existing:
            counter += 1

        return f"{base} ({counter})"
