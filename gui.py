import sys
from datetime import datetime

from PySide6.QtWidgets import(QApplication, QMainWindow, QWidget, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame)

class PassCoreUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PassCore vault")
        self.resize(1100, 700)
        self.build_ui()

    def build_ui(self):

        # Main Window Theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8FA;
            }
        """)

        # Menu Bar
        menu = self.menuBar()
        menu.addMenu("File")
        menu.addMenu("Edit")
        menu.addMenu("View")
        menu.addMenu("Help")

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
                border: 2px solid #D8B8C4;
                border-radius: 8px;
                padding: 8px;
                font-family: "JetBrains Mono";
                font-size: 12pt;
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
        self.lock_btn.clicked.connect(self.vault_lock)
        self.unlock_btn.clicked.connect(self.unlock_vault)
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

    # ==================================================
    # Actions
    def vault_lock(self):
        self.editor.setReadOnly(True)
        self.save_btn.setEnabled(False)

        self.status_label.setText("Locked")
        self.status_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                color: #C0392B;
                font-size: 15pt;
                font-weight: bold;
            }
        """)

    def unlock_vault(self):
        self.editor.setReadOnly(False)
        self.save_btn.setEnabled(True)

        self.status_label.setText("Unlocked")
        self.status_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                color: #27AE60;
                font-size: 15pt;
                font-weight: bold;
            }
        """)

    def save_vault(self):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.save_label.setText(
            f"Last Save\n{timestamp}"
        )

    def vault_close(self):
        self.close()


app = QApplication(sys.argv)
window = PassCoreUI()
window.show()

sys.exit(app.exec())