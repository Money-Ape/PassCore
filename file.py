import zipfile, shutil, tempfile, json
from pathlib import Path
from backup import CONTAINER_DIR, META_FILE, SALT_FILE, secure_del_tree
from PySide6.QtWidgets import (QMessageBox, QFileDialog)

def import_txt(window):
        if window.key is None:
            QMessageBox.information(window, "PassCore", "Unlock the vault before importing...")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            window, "Import any text File", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return
        
        reply = QMessageBox.question(
            window, "Import Records", "Replace current vault contents.?\n\nYes : Replace\nNo : Add", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Cancel:
            return
        
        try:
            with open(file_path, "r") as read_imp:
                imported_txt = read_imp.read()
            
            if reply == QMessageBox.Yes:
                window.editor.setPlainText(imported_txt)
            
            else:
                content_txt = window.editor.toPlainText()
                if content_txt.strip():
                    window.editor.setPlainText(
                        content_txt.rstrip() + "\n" + imported_txt
                    )
                else:
                    window.editor.setPlainText(imported_txt)
            
            QMessageBox.information(window, "PassCore", "Records imported successfully.!")

        except Exception as e:
            QMessageBox.critical(window, "Import Failed", str(e))

def import_pcv(window):    
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Import PassCore Vault", "","*.pcv"
    )
    if not file_path:
        return
    
    reply = QMessageBox.question(
        window, "Import PassCore Vault", "This will replace the current vault.\n\nContinue.?", QMessageBox.Yes | QMessageBox.No
    )
    if reply != QMessageBox.Yes:
        return
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, "r") as archive:
                archive.extractall(temp_dir)
            temp_dir = Path(temp_dir)
        
            temp_meta = temp_dir / "meta.json"
            temp_salt = temp_dir / "vault.salt"

            if not temp_meta.exists():
                raise RuntimeError("meta.json is missing from the vault")
            
            if not temp_salt.exists():
                raise RuntimeError("vault.salt is missing from the vault")
            
            if META_FILE.exists():
                META_FILE.unlink()

            if SALT_FILE.exists():
                SALT_FILE.unlink()
            
            if CONTAINER_DIR.exists():
                secure_del_tree(CONTAINER_DIR)

            shutil.copy2(temp_meta, META_FILE)
            shutil.copy2(temp_salt, SALT_FILE)

            with open(temp_meta, "r") as meta:
                metadata = json.load(meta)
                containers = {
                    info["container"]
                    for info in metadata["blobs"].values()
                }

                CONTAINER_DIR.mkdir(parents=True, exist_ok=True)
                for container in containers:
                    path = Path(temp_dir / container)
                    if not path.exists():
                        raise RuntimeError(f"Missing container : {container}")
                    else:
                        shutil.copytree(temp_dir / container, CONTAINER_DIR / container)
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
        window, "Export PassCore Vault", "PassCore_vault.pcv", "*.pcv"
    )
    if not file_path:
        return
    
    if not file_path.endswith(".pcv"):
        file_path += ".pcv"
    
    try:
        with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as export_to_zip: # writes splitted blobs into zipfile for backup
            export_to_zip.write(SALT_FILE, arcname=SALT_FILE.name)
            export_to_zip.write(META_FILE, arcname=META_FILE.name)

            for file in CONTAINER_DIR.rglob("*"):
                if file.is_file():
                    export_to_zip.write(file, arcname=file.relative_to(CONTAINER_DIR))
        
        QMessageBox.information(window, "PassCore", f"Vault exported successfully.\n\n{file_path}")

    except Exception as e:
        QMessageBox.critical(window, "Export Failed.!", str(e))