import sys, os, subprocess, json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import(QApplication, QMainWindow, QMenu, QWidget, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QDialog, QCheckBox, QLineEdit, QMessageBox, QSpinBox, QInputDialog, QListWidget, QListWidgetItem)
from PySide6.QtGui import QAction, QIcon, QTextCursor
from PySide6.QtCore import QTimer, Qt
from backup import create_backup, restore_backup, META_FILE
from passgen import generate_password
from health import vault_health
from file import import_txt, import_pcv, export_pcv
from settings import load_settings, save_settings

class PassCoreUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PassCore vault")
        self.setWindowIcon(
            QIcon("assets/PassCore.ico")
        )
        self.resize(1300, 800)
        self.settings = load_settings()
        self.autolock_timer = QTimer()
        
        self.build_ui()
        self.lock_screen = (
            "mww mww hwm wwl mwwMmwwww wwwmmmwww mwww wwl w wlwwww\n"
            "wwwww nwwwwwww n lwwwww w wwwww mwww nwwwwwww Nw mww w lwwww nwwwww\n"
            "wwww wwwwww w wwwwwwww wwwwww wwww w w w wwwwww\n"
            "nralq hwemi xouar mwehn ilqra uxmwo lhewr qnaim xoura mhnew"
            "lwwww wwwwww w wwwwww wwwwwwwwwww wwwwww Mwww wwwwww\n"
            "lwwww wwwwwwwwwwwwww Mwwwwwwwwwwwwwwww Mwww wwwwww\n\n"
            "wwwl wwww Mwww lwwww w wwwwwwwwwwwwww w wwwwwwww mwww wwww lwwwww\n"
            "mhae qrnli xouar mhnew ilaqr uxwmo qreni hlnwr qmrai woehn ilaqx murnw qlaei"
            "lwwwww w lwwwww wwww wwwwwwwwwwwwwwwww wwww wwwwwwwwww wwwwww Wwww\n"
            "wwwwwwwwwww wwww w wwwww wwww wwwwwwwwwwwwww Mwwwwww wwwww w www lwwwwwwww\n"
            "wwww wwww lwwww www lwwwwwwwwwwwwwwww wwwwwww wwwww wwwwwwww N w\n"
            "wwwwww wwwwwwwwww\n\n"
            "wlaeq hrnmi xouar mnewh ilaqr uxwmo mhawe qrnli xouar mhnew ilaqx"
            "w wwwwww w w wwwww wwwwwwww Mwww Mwww lwwww wwww w wwwwwwwwwwwwww\n"
            "w wwwwwwwwww Mwww wwww lwwwwwwww w wwwwwwww wwww wwwwwwwwwwww\n"
            "Mwwwwwwwwwwww Mwww w wwwww wwww wwwwwwwwwwwwwwww Mwwwwww wwwww w www\n"
            "nralq hwemi xouar mwehn ilqra uxmwo lhewr qnaim xoura mhnew ilaqx"
            "wwwwwwwwww wwwwww www w www wwwwww wwwww Mwwww wwwww\n"
            "wwwwwwwwwwwww wwwwwwwwwwwwww Mwwww www.\n\n"
            "xuaem hlnwr qmrai woehn ilaqx murnw qlaei mhawe qrnli xouar mhnew ilaqx"
            "w lwwwww wwwwwww w wwwwwwww w wwwwwww wwww wwwwwwww w wwww w\n"
            "Mwww wwwwwww wwww w wwwwwwwwww wwwwwwwww wwww wwwwwwww wwww M w w\n"
            "Mwwww wwwwwwwwww wwww w wwwwwwwww wwwwwwwwwwwwwwww w wwwwwwwwwww Mwww\n"
            "qreim xonua hmrwe inuia lxqro haemn qlwir xouma rnhew ilaqr umxwo"
            "wwww wwwwww w wwwwwwww wwwwwwwwwwww w wwwwwwwwwww wwwwww\n"
            "xuaem hlnwr qmrai woehn ilaqx murnw qlaei mhawe qrnli xouar"
            "mhae qrnli xouar mhnew ilaqr uxwmo qreni hlnwr qmrai"
            "wwwwwwwwwwwwwwwww wwwwwwwwwwwwwwwww wwwwww www\n"
        )
        self.update_vault_size()
        self.vault_text = None
        self.editor.setPlainText(self.lock_screen)
        self.key = None
        self.matches = []
        self.current_match = 0

    def build_ui(self):

        # Main Window Theme
        self.setStyleSheet("""        
            QWidget {
                background-color: #0B1120;
                color: #E5E7EB;
            }
            QMenuBar {
                background-color: #111827;
                color: #E5E7EB;
            }
            QMenuBar::item {
                background: transparent;
                color: #E5E7EB;
                padding: 6px 10px;
            }
            QMenuBar::item:selected {
                background-color: #D4AF37;
                color: #111827;
                border-radius: 4px;
            }
            QMenu {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #374151;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #D4AF37;
                color: #111827;
            }
        """)

        # Menu Bar
        menu = self.menuBar()
        file_menu = menu.addMenu("File") # File Menu
        import_action = QAction("Import text", self) # File menu : Import text files
        import_action.triggered.connect(lambda: import_txt(self))
        file_menu.addAction(import_action)

        import_vault_action = QAction("Import Vault", self) # Import Vault
        import_vault_action.triggered.connect(self.import_vault_handler)
        file_menu.addAction(import_vault_action)

        export_action = QAction("Export Vault", self) # File menu : Export PassCore Vault
        export_action.triggered.connect(lambda: export_pcv(self))
        file_menu.addAction(export_action)

        settings_menu = file_menu.addMenu("Settings") # File menu : Settings menu
        autolock_action = QAction("Auto-Lock Timer", self)
        autolock_action.triggered.connect(self.change_autolock_timer)
        settings_menu.addAction(autolock_action)
                
        edit_menu = menu.addMenu("Edit") # Edit Menu 
        create_backup_action = QAction("Create Backup", self) # Edit menu : Create Backup
        create_backup_action.triggered.connect(self.create_backup_now)
        edit_menu.addAction(create_backup_action)

        search_action = QAction("Search", self) # Edit menu : Search Menu
        search_action.setShortcut("Ctrl+F") # Search Shortcut key
        search_action.triggered.connect(self.toggle_search)
        edit_menu.addAction(search_action)
        
        restore_backup_action = QAction("Restore Backup", self) # Edit menu : Restore Backup
        restore_backup_action.triggered.connect(self.restore_backup_now)
        edit_menu.addAction(restore_backup_action)
        
        view_menu = menu.addMenu("View") # View Menu
        backup_folder_action = QAction("Open Backup Folder", self) # View menu : Backup folder lookup
        backup_folder_action.triggered.connect(self.open_backup_folder)
        view_menu.addAction(backup_folder_action)
        
        tools_menu = menu.addMenu("Tools") # Tools Menu
        pass_gen_action = QAction("Password Generator", self) # Tool menu : Password Generator
        pass_gen_action.triggered.connect(self.open_passwd_gen)
        tools_menu.addAction(pass_gen_action)

        vault_health_action = QAction("Vault Health", self) # Tool menu : Vault health report
        vault_health_action.triggered.connect(self.show_vault_health)
        tools_menu.addAction(vault_health_action)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        # ==================================================
        # Editor
        self.note_title = QLineEdit()
        self.note_title.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                color: #f9fafb;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #14b8a6;
            }
        """)

        self.note_title.setPlaceholderText("Note Title")

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Vani says Fahfah fah fah faaaah"
        )
        self.editor.setReadOnly(True)

        self.editor.setStyleSheet("""
            QTextEdit {
                background: #1A2233;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 10px;
                font-family: "JetBrains Mono";
                font-size: 12pt;
                selection-background-color: #D4AF37;
                selection-color: #202020;
            }
        """)
        # Notes
        self.current_note = 0
        self.notes = [{
            "title": "Untitled Note",
            "content": ""
        }]

        # Left Panel for Notes
        self.note_title.textChanged.connect(self.rename_note)
        self.add_note_btn = QPushButton("+")
        self.add_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f2937;
                color: white;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #374151;
            }
            QPushButton:pressed {
                background-color: #4b5563;
            }
        """)
        
        self.note_list = QListWidget()
        self.note_list.setStyleSheet("""
            QListWidget {
                background-color: #0B1120;
                color: #e5e7eb;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #1f2937;
            }
            QListWidget::item:selected {
                background-color: #d4af37;
                color: #111827;
            }
        """)

        self.note_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list.customContextMenuRequested.connect(self.note_context_menu)

        self.add_note_btn.clicked.connect(self.add_note)
        self.note_list.addItem("Untitled Note")
        self.note_list.currentRowChanged.connect(self.load_note)
        self.note_list.setCurrentRow(0)

        # Notes Layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.add_note_btn)
        left_layout.addWidget(self.note_list)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.note_title)
        right_layout.addWidget(self.editor)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 4)

        root_layout.addLayout(main_layout, stretch=4)

        # ==================================================
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0B1120;
                border: 1px solid #1f2937;
                border-radius: 10px;
            }
            QLabel {
                color: #e5e7eb;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)

        # Common Label Style
        self.info_style = """
            QLabel {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
                color: #E5E7EB;
                font-size: 11pt;
            }
        """

        # ==================================================
        # Date
        current_date = datetime.now().strftime("%d-%m-%Y")

        self.date_label = QLabel(
            f"Date\n{current_date}"
        )
        self.date_label.setStyleSheet(self.info_style)

        # ==================================================
        # Status
        self.status_label = QLabel("Locked")
        self.status_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                color: #D4AF37;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        # ==================================================
        # Vault Size
        self.size_label = QLabel(
            "Size\n0 bytes"
        )
        self.size_label.setStyleSheet(self.info_style)        

        # ==================================================
        # Last Save
        self.save_label = QLabel(
            "Last Save\n--"
        )
        self.save_label.setStyleSheet(self.info_style)

        # ==================================================
        # Search Rec
        self.search_input = QLineEdit() # Search Input
        self.match_label = QLabel("0 / 0") # Match text counts
        self.match_label.setStyleSheet("""
            QLabel {
                background: #FFF8FA;
                color: #C0392B;
                border: 2px solid #D8B8C4;
                border-radius: 8px;
                padding: 4px;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        
        self.prev_btn = QPushButton("◀") # Previous jump button
        self.prev_btn.setFixedWidth(60)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: #5D6D7E;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #708090;
            }
            QPushButton:pressed {
                background: #4A5568;
            }
        """)
        self.prev_btn.clicked.connect(self.prev_match)

        self.next_btn = QPushButton("▶") # Next jump button
        self.next_btn.setFixedWidth(60)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: #5D6D7E;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #708090;
            }
            QPushButton:pressed {
                background: #4A5568;
            }
        """)
        self.next_btn.clicked.connect(self.next_match)

        self.search_input.hide()
        self.match_label.hide()
        self.prev_btn.hide()
        self.next_btn.hide()

        self.search_input.setPlaceholderText("Search...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #F7E6EA;
                border: 2px solid #D8B8C4;
                border-radius: 8px;
                padding: 6px;
                color: #202020;
            }
        """)
        search_nav_layout = QHBoxLayout()
        search_nav_layout.addWidget(self.match_label)
        search_nav_layout.addStretch()

        search_nav_layout.addWidget(self.prev_btn)
        search_nav_layout.addWidget(self.next_btn)

        self.search_input.textChanged.connect(self.search_rec)

        # ==================================================
        # Sidebar layout
        sidebar_layout.addWidget(self.date_label) # Date label
        sidebar_layout.addWidget(self.status_label) # Vault Status label
        sidebar_layout.addWidget(self.size_label) # Size label
        sidebar_layout.addWidget(self.save_label) # Last-save label

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input) # Search input to sidebar 

        sidebar_layout.addLayout(search_layout)
        sidebar_layout.addLayout(search_nav_layout)
        sidebar_layout.addStretch()

        # ==================================================
        # Buttons
        self.lock_btn = QPushButton("Lock")
        self.unlock_btn = QPushButton("Unlock")
        self.save_btn = QPushButton("Save")
        self.close_btn = QPushButton("Close")

        self.save_btn.setEnabled(False)

        # Connections
        self.save_btn.clicked.connect(self.save_vault)
        self.close_btn.clicked.connect(self.vault_close)

        # Lock Button
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background: #d9534f;
                background-color: #1f2937;
                color: #d4af37;
                border: 2px solid #374151;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #273549;
            }
        """)

        # Unlock Button
        self.unlock_btn.setStyleSheet("""
            QPushButton {
                background: #5cb85c;
                color: black;
                border: 2px solid black;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #70c670;
            }
        """)

        # Save Button
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #7ea6e0;
                background-color: #d4af37;
                color: #111827;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e6c65c;
            }
            QPushButton:pressed {
                background-color: #b8941f;
            }
        """)

        # Close Button
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #d6d6d6;
                background-color: #374151;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)

        # Button Layouts
        row_1 = QHBoxLayout()
        row_1.addWidget(self.lock_btn)
        row_1.addWidget(self.unlock_btn)

        row_2 = QHBoxLayout()
        row_2.addWidget(self.save_btn)
        row_2.addWidget(self.close_btn)

        sidebar_layout.addLayout(row_1)
        sidebar_layout.addLayout(row_2)

        root_layout.addWidget(sidebar)

    def add_note(self):
        if self.current_note >= 0:
            current = self.notes[self.current_note]

        if not current["content"].strip():
            QMessageBox.information(self, "PassCore", "Current note is empty.!")
            return
        
        self.notes.append({
            "title": "Untitled Note",
            "content": ""
        })
        item = QListWidgetItem("Untitled note")
        self.note_list.addItem(item)
        self.note_list.setCurrentRow(self.note_list.count() - 1)

    def rename_note(self):
        if self.current_note < 0:
            return
        
        title = self.note_title.text().strip()
        if not title:
            title = "Untitled Note"
        
        self.notes[self.current_note]["title"] = title

        item = self.note_list.item(self.current_note)
        if item:
            item.setText(title)

    def load_note(self, row): # Switch b/w notes already loaded into mem.
        if row < 0:
            return
        
        if self.current_note >= 0:
            self.save_current_note()

        self.current_note = row
        note = self.notes[row]
        self.note_title.setText(note["title"])
        self.editor.setPlainText(note["content"])

    def load_notes(self, notes): # Loads the entire vault for Decryption.
        self.notes = notes
        self.note_list.clear()

        for note in notes:
            self.note_list.addItem(note["title"])
        
        self.current_note = -1
        self.note_list.setCurrentRow(0)

    def save_current_note(self):
        if not self.notes:
            return
        
        if self.current_note < 0:
            return

        if self.current_note >= len(self.notes):
            return
        
        note = self.notes[self.current_note]
        note["title"] = self.note_title.text()
        note["content"] = (self.editor.toPlainText())

    def note_context_menu(self, pos):
        item = self.note_list.itemAt(pos)
        if not item:
            return
        
        row = self.note_list.row(item)
        menu = QMenu(self)

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.note_list.mapToGlobal(pos))
        if action == rename_action:
            self.note_list.setCurrentRow(row)
            self.note_title.setFocus()

        if action == delete_action:
            reply = QMessageBox.question(
                self, "PassCore Note", f"Are you sure?\n\nDelete: {self.notes[row]["title"]}", QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            else:
                self.delete_note(row)

    def delete_note(self, row):
        if self.notes[row]["title"] == "Locked":
            return
        
        if len(self.notes) <= 1:
            return

        del self.notes[row]
        self.note_list.takeItem(row)
        
        row = max(0, min(row, len(self.notes) - 1))
        self.current_note = row
        self.note_list.setCurrentRow(row)

    def show_vault_health(self):
        dialog = VaultHealthDialog()
        dialog.exec()

    def open_passwd_gen(self):
        dialog = PasswordGenerator()

        if dialog.exec():
            password = dialog.output.text()
            self.editor.insertPlainText(password)

    def create_backup_now(self):
        create_backup()
        self.update_vault_size()

    def restore_backup_now(self):
        restore_backup(self)
        
        self.update_vault_size()

    def open_backup_folder(self):
        backup_dir = Path.home() / "Documents" / "PassCore Backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("linux"):
            subprocess.Popen(
                ["xdg-open", str(backup_dir)]
            )
        elif sys.platform == "win32":
            os.startfile(backup_dir)
        
        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(backup_dir)]
            )

    def vault_corrupted(self):
        self.key = None
        self.status_label.setText(
            "Corrupted"
        )
        self.status_label.setStyleSheet("""
            QLabel {
                border: None;
                background: transparent;
                color: #E67E22;
                font-size: 15pt;
                font-weight: bold;                         
            }
        """)
        self.size_label.setText("Size:\n0 bytes")
        self.size_label.setStyleSheet(self.info_style)
        self.editor.setReadOnly(True)
        self.editor.setPlainText(
            "Vault Integrity Verification Failed.!",
        )
        self.lock_btn.hide()
        self.unlock_btn.show()
        self.save_btn.hide()
        self.close_btn.setEnabled(True)

    def size_calc(self, size):
        units = ["Bytes", "KB", "MB", "GB", "TB"]
        for unit in units:
            if size < 1024 or unit == "TB":
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def update_vault_size(self):
        if not META_FILE.exists():
            self.size_label.setText(
                "Size\n0 bytes"
            )
            return
            
        with open(META_FILE, "r") as meta:
            vault_meta = json.load(meta)
        
        size = vault_meta.get("total_size", 0)
        read_size = self.size_calc(size)
        self.size_label.setText(
            f"Size\n{read_size}"
        )

    def save_vault(self):
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        self.save_label.setText(
            f"Last Save\n{timestamp}"
        )
        self.update_vault_size()

    def vault_close(self):
        self.close()

    def toggle_search(self):
        visible = self.search_input.isVisible()

        self.search_input.setVisible(not visible)
        self.match_label.setVisible(not visible)
        self.prev_btn.setVisible(not visible)
        self.next_btn.setVisible(not visible)

        if not visible:
            self.search_input.clear()
            self.matches = []
            self.current_match = -1
            self.match_label.setText("0 / 0")
            self.search_input.setFocus()

    def search_rec(self):        
        text = self.search_input.text().strip()
        if not text:
            self.matches = []
            self.current_match = -1
            self.match_label.setText("0 / 0")
            return
        
        content = self.editor.toPlainText()
        self.matches = []
        start = 0
        while True:
            pos = content.lower().find(text.lower(), start)
            if pos == -1:
                break
            
            self.matches.append(pos)
            start = pos + len(text)

        if not self.matches:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.match_label.setText("0 / 0")
            return
        
        self.current_match = 0
        self.goto_match()
        self.match_label.setText(
            f"{self.current_match + 1}/{len(self.matches)}"
        )

    def goto_match(self):
        if not self.matches:
            return
        
        pos = self.matches[self.current_match]
        cursor = self.editor.textCursor()
        cursor.setPosition(pos)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            len(self.search_input.text())
        )
        self.editor.setTextCursor(cursor)
        # self.editor.setFocus()

    def prev_match(self):
        if not self.matches:
            return
        self.current_match -= 1
        if self.current_match < 0:
            self.current_match = len(self.matches) - 1

        self.goto_match()
        self.match_label.setText(
            f"{self.current_match + 1}/{len(self.matches)}"
        )

    def next_match(self):
        if not self.matches:
            return
        self.current_match += 1
        if self.current_match >= len(self.matches):
            self.current_match = 0
        
        self.goto_match()
        self.match_label.setText(
            f"{self.current_match + 1}/{len(self.matches)}"
        )

    def import_vault_handler(self):
        success = import_pcv(self)
        if not success:
            return

        self.editor.setPlainText(
            self.lock_screen
        )
        self.editor.setReadOnly(True)
        self.key = None
        self.status_label.setText("Locked")
        self.lock_btn.hide()
        self.unlock_btn.show()
        self.save_btn.hide()
        self.close_btn.setEnabled(True)

        self.note_list.clear()
        self.note_title.clear()
        self.notes = [{
            "title": "Locked",
            "content": ""
        }]

        QMessageBox.information(self, "PassCore", "Import complete.\n\nUnlock the imported vault to continue.")

    def change_autolock_timer(self):
        current = self.settings["auto_lock_min"]

        minutes, ok = QInputDialog.getInt(
            self, "Auto-Lock Timer",
            "Minutes: ", current,
            1, 120
        )
        if not ok:
            return
        
        self.settings["auto_lock_min"] = minutes
        save_settings(self.settings)
        if self.key is not None: 
            self.autolock_timer.setInterval(minutes * 60 * 1000)
        
        QMessageBox.information(
            self,"PassCore", f"Auto-Lock Timer set to {minutes} minute(s)."
        )            

class PasswordDialog(QDialog):
    def __init__(self, title="PassCore Vault", confirm=False):
        super().__init__()
        self.confirm = confirm
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon("assets/PassCore.png"))
        self.setStyleSheet("""
            background-color: #111827;
            color: #E5E7EB;
            border-bottom: 1px solid #374151;
        """)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        if self.confirm:
            self.confirm_password = QLineEdit()
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_pass = QCheckBox("Show Password")
        self.unlock_btn = QPushButton("Ok")
        self.cancel_btn = QPushButton("Cancel")

        self.show_pass.toggled.connect(self.toggle_password)
        self.unlock_btn.clicked.connect(self.validate_passwd)
        self.cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Master Password")) # Master Password Dialog
        layout.addWidget(self.password) # Password Input

        if self.confirm:
            layout.addWidget(QLabel("Confirm Password"))
            layout.addWidget(self.confirm_password)
            
        layout.addWidget(self.show_pass) # Checkbox Input

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def toggle_password(self, checked):
        mode = (QLineEdit.EchoMode.Normal
            if checked
            else QLineEdit.EchoMode.Password
        )
        self.password.setEchoMode(mode)
        
        if self.confirm:
            self.confirm_password.setEchoMode(mode)

    def validate_passwd(self):
        if self.confirm:
            if (self.password.text() != self.confirm_password.text()):
                QMessageBox.warning(
                    self, "PassCore", "Your Password doesn't match with your vault password...\nDon't play with passwrrd passwrod password*"
                )
                return
        self.accept()

class PasswordGenerator(QDialog):

    def __init__(self, title="PassCore Password Generator"):
        super().__init__()
        self.setWindowTitle(title)
        self.setStyleSheet("""
            QDialog {
                background-color: #0B1120;
                color: #E5E7EB;
            }
            QLabel {
                color: #E5E7EB;
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #D4AF37;
            }
            QCheckBox {
                color: #E5E7EB;
            }
            QPushButton {
                background-color: #1F2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2B3648;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
        """)
        self.lenght_spin = QSpinBox()
        self.lenght_spin.setRange(8, 128)
        self.lenght_spin.setValue(19)

        self.upper_ch = QCheckBox("Uppercase")
        self.lower_ch = QCheckBox("Lowercase")
        self.digits_ch = QCheckBox("Numbers")
        self.symbols_ch = QCheckBox("Symbols")
        
        self.upper_ch.setChecked(True)
        self.lower_ch.setChecked(True)
        self.digits_ch.setChecked(True)
        self.symbols_ch.setChecked(True)

        self.output = QLineEdit()
        self.output.setReadOnly(True)

        self.generate_btn = QPushButton("Generate") # Buttons
        self.insert_btn = QPushButton("Insert")
        self.cancel_btn = QPushButton("Cancel")

        self.generate_btn.clicked.connect(self.generate_passwd) # Connections
        self.insert_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout() # Vertical layout for User Actions
        layout.addWidget(QLabel("Password Length"))

        layout.addWidget(self.lenght_spin)
        layout.addWidget(self.upper_ch)
        layout.addWidget(self.lower_ch)
        layout.addWidget(self.digits_ch)
        layout.addWidget(self.symbols_ch)

        layout.addWidget(QLabel("Generate Password"))
        layout.addWidget(self.output)

        btn_layout = QHBoxLayout() # Horizontal layout for User Actions
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.insert_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.generate_passwd()

    def generate_passwd(self):
        password = generate_password(
            length=self.lenght_spin.value(),
            upper=self.upper_ch.isChecked(),
            lower=self.lower_ch.isChecked(),
            digits=self.digits_ch.isChecked(),
            symbols=self.symbols_ch.isChecked(),
        )
        self.output.setText(password)

class VaultHealthDialog(QDialog):

    def __init__(self):
        super().__init__()
        report = vault_health()
        self.setWindowTitle("Vault Health")
        self.setFixedSize(500, 550)

        score = report["score"]

        if score == 100:
            health = "🟢 HEALTHY"
            color = "#4CAF50"

        elif score >= 80:
            health = "🟡 WARNING"
            color = "#FBC02D"

        else:
            health = "🔴 CRITICAL"
            color = "#E53935"

        self.setStyleSheet("""
            QDialog {
                background-color: #0B1120;
            }
            QFrame {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
            }
            QLabel {
                color: #E5E7EB;
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #D4AF37;
                color: #111827;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E6C65C;
            }
            QPushButton:pressed {
                background-color: #B8941F;
            }
        """)

        # ==========================================
        # Health Status
        status_label = QLabel(health)
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 20pt;
                font-weight: bold;
            }}
        """)

        score_label = QLabel(
            f"Score: {score}/100"
        )
        score_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #E5E7EB;
            }
        """)

        # ==========================================
        # Vault Information
        info_frame = QFrame()
        info_layout = QVBoxLayout()

        info_title = QLabel(
            "Vault Information"
        )
        info_title.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                font-weight: bold;
                color: #D4AF37;
            }
        """)

        info_label = QLabel(f"""
            Created : {report['created']}
            Modified: {report['modified']}

            Blobs   : {report['blob_count']}
            Size    : {report['total_size']} bytes
            Backups : {report['backups']}
            """
        )
        info_label.setStyleSheet("""
            QLabel {
                font-family: monospace;
                font-size: 11pt;
                color: #C9D1D9;
            }
        """)
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_label)

        info_frame.setLayout(info_layout)

        # ==========================================
        # Integrity Checks
        checks_frame = QFrame()
        checks_layout = QVBoxLayout()

        checks_title = QLabel("Integrity Checks")
        checks_title.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                font-weight: bold;
                color: #D4AF37;
            }
        """)

        checks_layout.addWidget(checks_title)
        checks = [
            ("Metadata", report["metadata"]),
            ("Containers", report["containers"]),
            ("Blobs", report["existence"]),
            ("Blob Size", report["size"]),
            ("SHA256", report["sha256"])
        ]
        for name, passed in checks:
            status = (
                "✓ PASS"
                if passed
                else "✗ FAIL"
            )
            color = (
                "#4CAF50"
                if passed
                else "#E53935"
            )
            label = QLabel(f"{name:<12} {status}")
            label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 11pt;
                    font-family: monospace;
                }}
            """)

            checks_layout.addWidget(label)

        checks_frame.setLayout(checks_layout)

        # ==========================================
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        # ==========================================
        # Main Layout
        layout = QVBoxLayout()

        layout.addWidget(status_label)
        layout.addWidget(score_label)
        layout.addWidget(info_frame)
        layout.addWidget(checks_frame)

        layout.addStretch()
        layout.addWidget(close_btn)
        self.setLayout(layout)
    
    def refresh(self):
        self.close()
        dialog = VaultHealthDialog()
        dialog.exec()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassCoreUI()
    window.show()

    sys.exit(app.exec())
