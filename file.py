import platform, os
from pathlib import Path
from PySide6.QtWidgets import (QMessageBox, QFileDialog)
from security.yaml_secure import secure_load, convert_yaml_to_text, VaultValidationError

def get_PassCore_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / "passcore"
    
    elif sys == "Windows":
        return Path(os.getenv("APPDATA")) / "PassCore"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

def get_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_container_dir()
PASSCORE_DIR = get_PassCore_dir()

CONTAINER_DIR.mkdir(parents=True, exist_ok=True)
PASSCORE_DIR.mkdir(parents=True, exist_ok=True)
SALT_FILE = PASSCORE_DIR / "vault.salt"
META_FILE = PASSCORE_DIR / "notes_index.json"
SETTINGS = PASSCORE_DIR / "settings.yaml"
IMAGES_META = PASSCORE_DIR / "images_index.json"

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

def import_txt(window):
        if window.key is None:
            QMessageBox.information(window, "PassCore", "Unlock the vault before importing...")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            window, "Import any text File", "", "Text Files (*.txt);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not file_path:
            return
        
        reply = QMessageBox.question(
            window, "Import Records", "Replace current vault contents.?\n\nYes -> Replace current note\nNo -> Add into existing one\nCancel -> Abort", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Cancel:
            return
        
        try:
            with open(file_path, "r") as read_imp:
                imported_txt = read_imp.read()

            try:
                parsed = secure_load(imported_txt)
                imported_txt = convert_yaml_to_text(parsed)

            except VaultValidationError as e:
                QMessageBox.critical(window, "Invalid YAML", str(e))
                return

            except Exception:
                # fallback: treat as plain text
                pass
            
            note_title = Path(file_path).stem
            if reply == QMessageBox.Yes:
                window.save_current_note()

                # Replace only the current selected note.
                window.notes[window.current_note]["title"] = note_title
                window.notes[window.current_note]["content"] = imported_txt

                # Update only current item in note_list
                item = window.note_list.item(window.current_note)
                item.setText(note_title)

                # Reload the editor.
                window.note_title.setText(note_title)
                window.editor.setPlainText(imported_txt)

            else:
                window.save_current_note()
                current_text = window.editor.toPlainText()
                if current_text.strip():
                    new_text = current_text + "\n\n" + imported_txt
                else:
                    new_text = imported_txt

                window.notes[window.current_note]["content"] = new_text
                window.editor.setPlainText(new_text)

                window.save_current_note()
            
            QMessageBox.information(window, "PassCore", "Records imported successfully.!")

        except Exception as e:
            QMessageBox.critical(window, "Import Failed", str(e))
