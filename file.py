import zipfile, shutil, tempfile, json, platform, os, backup
from pathlib import Path
from backup import META_FILE, SALT_FILE, SETTINGS, IMAGES_META, secure_del_tree
from PySide6.QtWidgets import (QMessageBox, QFileDialog)

def get_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db"
    
    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_container_dir()

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

def import_pcv(window):    
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Import PassCore Vault", "","PassCore Vault (*.pcv)",
        options=QFileDialog.Option.DontUseNativeDialog
    )
    if not file_path:
        return
    
    reply = QMessageBox.question(
        window, "Import PassCore Vault", "This will replace the current vault.\n\nContinue.?", QMessageBox.Yes | QMessageBox.No
    )
    if reply != QMessageBox.Yes:
        return
    
    try:
        with zipfile.ZipFile(file_path, "r") as archive:
            archive.extractall(CONTAINER_DIR)

        shutil.move(CONTAINER_DIR / "meta.json", META_FILE)
        shutil.move(CONTAINER_DIR / "vault.salt", SALT_FILE)
        shutil.move(CONTAINER_DIR / "settings.json", SETTINGS)
        shutil.move(CONTAINER_DIR / "images_index.json", IMAGES_META)

        return True
        
    except Exception as e:
        QMessageBox.critical(window, "Import Failed.!", str(e))
        return False

def export_pcv(window):
    if window.key is None:
        QMessageBox.information(window, "PassCore", "Unlock the vault before exporting...")
        return
    
    if not META_FILE.exists():
        QMessageBox.warning(window, "PassCore", "No vault available to export.!") # prevents exporting a corrupted/uninitialized vault state.

    file_path, _ = QFileDialog.getSaveFileName(
        window, "Export PassCore Vault", "PassCore_vault.pcv", "PassCore Vault (*.pcv)",
        options=QFileDialog.Option.DontUseNativeDialog
    )
    if not file_path:
        return
    
    if not file_path.endswith(".pcv"):
        file_path += ".pcv"
    
    try:
        with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as export_to_zip: # writes splitted blobs into zipfile for backup
            export_to_zip.write(SALT_FILE, arcname=SALT_FILE.name)
            export_to_zip.write(META_FILE, arcname=META_FILE.name)
            export_to_zip.write(SETTINGS, arcname=SETTINGS.name)
            export_to_zip.write(IMAGES_META, arcname=IMAGES_META.name)

            for file in CONTAINER_DIR.rglob("*"):
                if file.is_file():
                    export_to_zip.write(file, arcname=file.relative_to(CONTAINER_DIR))
        
        QMessageBox.information(window, "PassCore", f"Vault exported successfully.\n\n{file_path}")

    except Exception as e:
        QMessageBox.critical(window, "Export Failed.!", str(e))