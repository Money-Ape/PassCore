import sys, os, subprocess, json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import(QApplication, QMainWindow, QWidget, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QDialog, QCheckBox, QLineEdit, QMessageBox, QSpinBox)
from PySide6.QtGui import QAction, QIcon
from backup import create_backup, restore_backup, META_FILE
from passgen import generate_password
from health import generate_report

class PassCoreUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PassCore vault")
        self.setWindowIcon(
            QIcon("assets/PassCore.png")
        )
        self.resize(1100, 700)
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

    def build_ui(self):

        # Main Window Theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8FA;
                color: #202020;
            }
            QMenuBar {
                background: #FFF8FA;
                color: #202020;
            }
            QMenuBar::item {
                background: transparent;
                color: #202020;
                padding: 6px 10px;
            }
            QMenuBar::item:selected {
                background: #D8B8C4;
                border-radius: 4px;
            }
            QMenu {
                background: #FFF8FA;
                color: #202020;
                border: 2px solid #D8B8C4;
            }
            QMenu::item {
                padding: 6px 20px;
                color: #202020;
            }
            QMenu::item:selected {
                background: #D8B8C4;
                color: #202020;
            }
        """)

        # Menu Bar
        menu = self.menuBar()
        menu.addMenu("File")
        
        edit_menu = menu.addMenu("Edit")
        create_backup_action = QAction("Create Backup", self)
        create_backup_action.triggered.connect(self.create_backup_now)
        edit_menu.addAction(create_backup_action)
        
        restore_backup_action = QAction("Restore Backup", self)
        restore_backup_action.triggered.connect(self.restore_backup_now)
        edit_menu.addAction(restore_backup_action)
        
        view_menu = menu.addMenu("View")
        backup_folder_action = QAction("Open Backup Folder", self)
        backup_folder_action.triggered.connect(self.open_backup_folder)
        view_menu.addAction(backup_folder_action)
        
        tools_menu = menu.addMenu("Tools")
        pass_gen_action = QAction("Password Generator", self)
        pass_gen_action.triggered.connect(self.open_passwd_gen)
        tools_menu.addAction(pass_gen_action)

        vault_health_action = QAction("Vault Health", self)
        vault_health_action.triggered.connect(self.show_vault_health)
        tools_menu.addAction(vault_health_action)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        # ==================================================
        # Editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Vault Unlocked.!\nDo Editing..."
        )
        self.editor.setReadOnly(True)

        self.editor.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF;
                color: #202020;
                border: 2px solid #D8B8C4;
                border-radius: 8px;
                padding: 8px;
                font-family: "JetBrains Mono";
                font-size: 12pt;
                selection-background-color: #D8B8C4;
                selection-color: #202020;
            }
        """)

        root_layout.addWidget(self.editor, stretch=4)

        # ==================================================
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(230)

        sidebar.setStyleSheet("""
            QFrame {
                background: #FFECEF;
                border: 2px solid #D8B8C4;
                border-radius: 8px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)

        # Common Label Style
        info_style = """
            QLabel {
                background: #F7E6EA;
                border: 2px solid #D8B8C4;
                border-radius: 8px;
                padding: 6px;
                color: #4A4A4A;
                font-size: 11pt;
            }
        """

        # ==================================================
        # Date
        current_date = datetime.now().strftime("%d-%m-%Y")

        self.date_label = QLabel(
            f"Date\n{current_date}"
        )
        self.date_label.setStyleSheet(info_style)

        # ==================================================
        # Status
        self.status_label = QLabel("Locked")
        self.status_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                color: #C0392B;
                font-size: 15pt;
                font-weight: bold;
            }
        """)
        # ==================================================
        # Vault Size
        self.size_label = QLabel(
            "Size\n0 bytes"
        )
        self.size_label.setStyleSheet(info_style)        

        # ==================================================
        # Last Save
        self.save_label = QLabel(
            "Last Save\n--"
        )
        self.save_label.setStyleSheet(info_style)

        sidebar_layout.addWidget(self.date_label)
        sidebar_layout.addWidget(self.status_label)
        sidebar_layout.addWidget(self.size_label)
        sidebar_layout.addWidget(self.save_label)

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
                color: black;
                border: 2px solid black;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #e46b67;
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
                color: black;
                border: 2px solid black;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #92b5e7;
            }
        """)

        # Close Button
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #d6d6d6;
                color: black;
                border: 2px solid black;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #e4e4e4;
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

    def show_vault_health(self):
        report = generate_report()
        QMessageBox.information(
            self, "Vault Health", report
        )

    def open_passwd_gen(self):
        dialog = PasswordGenerator()

        if dialog.exec():
            password = dialog.output.text()
            self.editor.insertPlainText(password)

    def create_backup_now(self):
        create_backup()
        self.update_vault_size()

    def restore_backup_now(self):
        restore_backup()
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
        self.editor.setPlainText(
            "Vault Integrity Verification Failed.!",
        )

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
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.save_label.setText(
            f"Last Save\n{timestamp}"
        )
        self.update_vault_size()

    def vault_close(self):
        self.close()

class PasswordDialog(QDialog):
    def __init__(self, title="Unlock Vault", confirm=False):
        super().__init__()
        self.confirm = confirm
        self.setWindowTitle(title)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassCoreUI()
    window.show()

    sys.exit(app.exec())
