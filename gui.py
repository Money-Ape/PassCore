import sys
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QMenuBar)
from PySide6.QtCore import Qt

class PassCoreUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PassCore vault")
        self.resize(1100, 700)
        self.build_ui()

    def build_ui(self):
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

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Vault Unlocked.!\nDo Editting...")

        self.editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid black;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }        
        """)
        root_layout.addWidget(self.editor, stretch=4)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("""
            QTextEdit {
                border: 2px solid black;
                border-radus: 8px;                  
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.addStretch()

        # Date

        # Vault Status

        # Vault Size

        # Last Save


app = QApplication(sys.argv)
window = PassCoreUI()
window.show()

sys.exit(app.exec())