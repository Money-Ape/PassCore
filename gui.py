import sys, os, subprocess, json, ctypes
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import(QApplication, QMainWindow, QMenu, QWidget, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QDialog, QFileDialog, QCheckBox, QComboBox, QLineEdit, QMessageBox, QSpinBox, QInputDialog, QListWidget, QListWidgetItem, QToolButton, QProgressDialog, QScrollArea)
from PySide6.QtGui import QAction, QIcon, QTextCursor, QPixmap, QShowEvent, QColor, QTextCharFormat
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QPoint, QSize, Signal
from backup import create_backup, restore_backup, META_FILE, secure_del_tree
from passgen import generate_password
from health import vault_health
from file import import_txt, import_pcv, export_pcv
from settings import load_settings, save_settings
from theme import THEMES, BUTTONS
from pcvmenu.images import import_image, load_preview, IMAGES_META, CONTAINER_DIR
from flowlayout import FlowLayout
from collections import defaultdict

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PassCoreUI(QMainWindow):
    def __init__(self, vault_key=None):
        super().__init__()
        self.vault_key = vault_key

        print("MEIPASS:", getattr(sys, "_MEIPASS", "NOT SET"))
        print("ICON:", resource_path("assets/PassCore.ico"))
        print("EXISTS:", os.path.exists(resource_path("assets/PassCore.ico")))
        self.setWindowTitle("PassCore vault")
        self.setWindowIcon(
            QIcon(resource_path("assets/PassCore.ico"))
        )
        self.resize(1400, 850)
        self.settings = load_settings()
        self.autolock_timer = QTimer()
        self.WELCOME_TEXT = """
            Welcome to PassCore.!

            Maintainer : Lovepreet Singh aka Money-Ape

            • Create notes
            • Store credentials
            • Import text files
            • Export PassCore vaults
            • Create encrypted backups

            Your data never leaves your device.

            Thanks :)
        """.strip()
        self.apply_themes()
        self.current_section = "credentials"

        self.build_ui()
        self.menu_option = False
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
        self.selected_images = set()
        self.vault_text = None
        self.editor.setPlainText(self.lock_screen)
        self.key = None
        self.matches = []
        self.current_match = 0
        self.refresh_theme()

    def apply_themes(self):
        theme = THEMES[self.settings["theme"]]

        self.win = theme["window"]
        self.w = theme["workspace"]
        self.i = theme["interactive"]
        self.b = theme["border"]
        self.t = theme["text"]

        self.lock_theme = BUTTONS["lock"]
        self.unlock_theme = BUTTONS["unlock"]
        self.save_theme = BUTTONS["save"]
        self.close_theme = BUTTONS["close"]
        
        self.STATUS_COLORS = {
            "locked": "#D4AF37",
            "unlocked": "#4CAF50",
            "corrupted": "#E53935"
        }

        self.SEARCH_HIGHLIGHT = theme["search"]

    def refresh_theme(self):
        self.settings = load_settings()
        self.apply_themes()

        # Main Window Theme
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.win};
                color: {self.t};
            }}
            QMenuBar {{
                background-color: {self.win};
                color: {self.t};
                border: ;
            }}
            QMenuBar::item {{
                background: transparent;
                color: {self.t};
                padding: 6px 10px;
            }}
            QMenuBar::item:selected {{
                background-color: {self.i};
                color: {self.t};
                border-radius: 4px;
            }}
            QMenu {{
                background-color: {self.win};
                color: {self.t};
                border: 2px solid {self.b};
            }}
            QMenu::item {{
                padding: 6px 20px;
            }}
            QMenu::item:selected {{
                background-color: {self.i};
                color: {self.t};
            }}
        """)

        # Slide Menu btn
        self.menu_btn.setStyleSheet(f"""
            QToolButton {{
                color: {self.t};
                background: transparent;
                border: none;
                padding: 2px 4px;
                font-size: 13pt;
            }}
            QToolButton:hover {{
                background: {self.i};
                border-radius: 6px;
            }}
            QToolButton:pressed {{
                background: {self.b};
            }}
        """)

        # Slide Menubar
        self.slide_menu.setStyleSheet(f"""
            QFrame {{
                background-color: {self.i};

                border: 2px solid {self.b};

                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;

                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
        """)

        # Slide Menu btn
        for btn in self.slide_btn:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {self.t};
                    border: {self.b};
                    text-align: left;
                    padding: 8px;
                    font-size: 11pt;
                }}
                QPushButton:hover {{
                    background: {self.w};
                    border-radius: 6px;
                }}
            """)
        
        # Editor
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.w};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 10px;
                padding: 10px;
                font-family: "JetBrains Mono";
                font-size: 12pt;
            }}
            QScrollBar:vertical {{
                background: {self.w};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {self.i};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.t};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)

        # Welcome Editor message
        self.welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {self.t};
                background: transparent;
                border: none;
                font-size: 12pt;
                padding: 30px;
            }}
        """)

        # Note title
        self.note_title.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.t};
            }}
        """)

        # Note btn
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.w};
                border: 2px solid {self.b};
            }}
            QPushButton:pressed {{
                background-color: {self.i};
            }}
        """)

        # Note list
        self.note_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {self.w};
                color: {self.t};
            }}
            QListWidget::item:selected {{
                background-color: {self.t};
                color: {self.w};
                font-weight: bold;
            }}
        """)

        # Sidebar
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.w};
                border: 2px solid {self.b};
                border-radius: 10px;
            }}
            QLabel {{
                color: {self.t};
                background: transparent;
                border: none;
            }}
        """)

        # Common Label Style
        self.info_style = (f"""
            QLabel {{
                background-color: {self.w};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
                color: {self.t};
                font-size: 11pt;
            }}
        """)

        if self.status_label.text() == "Locked":
            color = self.STATUS_COLORS["locked"]

        elif self.status_label.text() == "Unlocked":
            color = self.STATUS_COLORS["unlocked"]

        else:
            color = self.STATUS_COLORS["corrupted"]

        # Status label
        self.status_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                background: transparent;
                color: {color};
                font-size: 18px;
                font-weight: bold;
            }}
        """)

        # Match label
        self.match_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.i};
                color: #E53935;
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 4px;
                font-weight: bold;
                font-size: 10pt;
            }}
        """)

        # Navigation btn
        self.nav_btn_style = (f"""
            QPushButton {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12pt;
            }}
            QPushButton:hover {{
                background-color: {self.w};
                border: 2px solid {self.b};
            }}
            QPushButton:pressed {{
                background-color: {self.t};
                color: {self.w};
            }}
        """)

        # Previous btn
        self.prev_btn.setStyleSheet(self.nav_btn_style)

        # Next btn
        self.next_btn.setStyleSheet(self.nav_btn_style)

        # Date label
        self.date_label.setStyleSheet(self.info_style)

        # Size label
        self.size_label.setStyleSheet(self.info_style)

        # Save label
        self.save_label.setStyleSheet(self.info_style)

        # Search bar
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.t};
            }}
            QLineEdit::placeholder {{
                color: {self.t};
            }}
        """)

        self.gallery_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.w};
                border: 2px solid {self.b};
                border-radius: 10px;
            }}
            QWidget {{
                background-color: {self.w};
            }}
            QScrollBar:vertical {{
                background: {self.w};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {self.i};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.t};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar:horizontal {{
                background: {self.w};
                height: 10px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {self.i};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {self.t};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                border: none;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """)

        # Image Selection Label.
        self.selection_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.i};
                color: {self.t};
                border: 1px solid {self.b};
                border-radius: 10px;
                padding: 6px 14px;
                font-size: 10pt;
                font-weight: bold;
            }}
        """)

        # Lock Button
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.lock_theme["bg"]};
                color: {self.lock_theme["text"]};
                border: 2px solid {self.b} ;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.lock_theme["hover"]};
            }}
        """)

        # Unlock Button
        self.unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.unlock_theme["bg"]};
                color: {self.unlock_theme["text"]};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.unlock_theme["hover"]};
            }}
        """)

        # Save Button
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.save_theme["bg"]};
                color: {self.save_theme["text"]};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.save_theme["hover"]};
            }}
        """)

        # Close Button
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.close_theme["bg"]};
                color: {self.close_theme["text"]};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.close_theme["hover"]};
            }}
        """)

        # Refresh search highlight.
        if self.search_input.isVisible() and self.matches:
            self.goto_match()

    def open_theme_dialog(self):
        dialog = ThemeDialog(self)

        if not dialog.exec():
            return

        selected_theme = dialog.theme_combo.currentData()
        if selected_theme == self.settings["theme"]:
            return

        self.settings["theme"] = selected_theme
        save_settings(self.settings)
        
        self.refresh_theme()

    def build_ui(self):

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        # Slide Menu
        self.SLIDE_MENU_WIDTH = 205
        self.slide_menu = QFrame(central)
        self.slide_menu.setObjectName("Slide Menu")
        self.slide_menu.setFixedWidth(self.SLIDE_MENU_WIDTH)

        self.menu_animation = QPropertyAnimation(self.slide_menu, b"pos")
        self.menu_animation.setDuration(self.SLIDE_MENU_WIDTH)
        self.menu_animation.setEasingCurve(QEasingCurve.OutCubic)


        self.slide_layout = QVBoxLayout(self.slide_menu)
        self.slide_layout.setContentsMargins(10, 10, 10, 10)
        self.slide_layout.addSpacing(8)
        self.slide_menu.setLayout(self.slide_layout)
        self.slide_menu_items()

        # Menu Bar
        menu = self.menuBar()
        self.menu_btn = QToolButton(self)
        self.menu_btn.setText("\u2630")
        self.menu_btn.setAutoRaise(True)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        menu.setCornerWidget(self.menu_btn, Qt.Corner.TopLeftCorner)
        self.menu_btn.clicked.connect(self.toggle_slide_menu)

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

        theme_action = QAction("Theme", self) # File menu : Themes
        theme_action.triggered.connect(self.open_theme_dialog)
        settings_menu.addAction(theme_action)

        capture_action = QAction("Hide from Screen capture/recording (Windows only)", self)
        capture_action.setCheckable(True)
        if os.name != "nt":
            capture_action.setEnabled(False)
            
        else:
            capture_action.setChecked(self.settings.get("hide_from_capture", False))
            capture_action.toggled.connect(self.toggle_capture_protection)
        
        settings_menu.addAction(capture_action)
                
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

        root_layout = QHBoxLayout(central)

        # ==================================================
        # Editor
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note Title")
        self.editor = QTextEdit()

        # Images Gallery
        self.gallery_widget = QWidget()
        self.gallery_layout = QVBoxLayout()
        self.gallery_layout.setContentsMargins(8, 8, 8, 8)
        self.gallery_layout.setSpacing(20)

        self.gallery_layout.addStretch()
        self.gallery_widget.setLayout(self.gallery_layout)

        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setWidget(self.gallery_widget)

        self.selection_label = QLabel(self.gallery_scroll.viewport())
        self.selection_label.hide()
        self.selection_label.adjustSize()

        self.gallery_scroll.hide()
        
        # Image Editor
        self.preview_widget = QWidget()
        preview_layout = QVBoxLayout(self.preview_widget)

        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.back_to_gallery)

        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_name = QLabel()
        self.preview_size = QLabel()
        self.preview_resolution = QLabel()
        self.preview_created = QLabel()

        preview_layout.addWidget(self.back_btn)        
        preview_layout.addWidget(self.image_preview, 1)

        preview_layout.addWidget(self.preview_name)        
        preview_layout.addWidget(self.preview_size)        
        preview_layout.addWidget(self.preview_resolution)        
        preview_layout.addWidget(self.preview_created)        

        self.preview_widget.hide()

        # Welcome GHost Message for Editor
        self.welcome_label = QLabel(
            self.WELCOME_TEXT, self.editor
        )
        self.welcome_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setGeometry(self.editor.rect())
        self.editor.textChanged.connect(self.update_welcome_label)

        # Notes
        self.current_note = 0
        self.notes = [{
            "title": "Untitled Note",
            "content": ""
        }]

        # Left Panel for Notes
        self.note_title.textChanged.connect(self.rename_note)
        self.add_btn = QPushButton("+")
        
        self.note_list = QListWidget()
        self.note_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_list.customContextMenuRequested.connect(self.item_context_menu)

        self.add_btn.clicked.connect(self.add_item)
        self.note_list.addItem("Untitled Note")
        self.note_list.currentRowChanged.connect(self.load_note)
        self.note_list.itemClicked.connect(self.load_album)
        self.note_list.setCurrentRow(0)

        # Notes Layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.add_btn)
        left_layout.addWidget(self.note_list)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.note_title)
        right_layout.addWidget(self.editor)
        right_layout.addWidget(self.gallery_scroll)
        right_layout.addWidget(self.preview_widget)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 4)

        root_layout.addLayout(main_layout, stretch=4)

        # ==================================================
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(self.sidebar)

        # ==================================================
        # Date
        current_date = datetime.now().strftime("%d-%m-%Y")

        self.date_label = QLabel(
            f"Date\n{current_date}"
        )

        # ==================================================
        # Status
        self.status_label = QLabel("Locked")
        
        # ==================================================
        # Vault Size
        self.size_label = QLabel(
            "Size\n0 bytes"
        )        

        # ==================================================
        # Last Save
        self.save_label = QLabel(
            "Last Save\n--"
        )

        # ==================================================
        # Search Rec
        self.search_input = QLineEdit() # Search Input
        self.match_label = QLabel("0 / 0") # Match text counts

        self.prev_btn = QPushButton("◀") # Previous jump button
        self.prev_btn.setFixedWidth(60)
        self.prev_btn.clicked.connect(self.prev_match)

        self.next_btn = QPushButton("▶") # Next jump button
        self.next_btn.setFixedWidth(60)
        self.next_btn.clicked.connect(self.next_match)

        self.search_input.hide()
        self.match_label.hide()
        self.prev_btn.hide()
        self.next_btn.hide()

        self.search_input.setPlaceholderText("Search...")
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

        # Button Layouts
        row_1 = QHBoxLayout()
        row_1.addWidget(self.lock_btn)
        row_1.addWidget(self.unlock_btn)

        row_2 = QHBoxLayout()
        row_2.addWidget(self.save_btn)
        row_2.addWidget(self.close_btn)

        sidebar_layout.addLayout(row_1)
        sidebar_layout.addLayout(row_2)

        root_layout.addWidget(self.sidebar)
        
        note_geo = self.note_list.geometry()
        self.slide_menu.setGeometry(
            -self.SLIDE_MENU_WIDTH, # hidden outside the window
            note_geo.y(), # just below the menubar
            self.SLIDE_MENU_WIDTH, # Drawer width
            note_geo.height()
        )
        self.slide_menu.raise_()

        self.update_welcome_label()

    # Credentials
    def show_credentials(self):
        self.reset_image_view()
        self.current_section = "credentials"
        self.add_btn.setText("+ Note")
        self.note_title.show()
        self.editor.show()
        self.save_label.show()

        self.gallery_scroll.hide()
        self.preview_widget.hide()

        self.load_notes(self.notes)

    # Return from image to preview gallery
    def back_to_gallery(self):
        self.preview_widget.hide()
        self.gallery_scroll.show()

        self.image_preview.clear()

    # Images
    def show_images(self):
        self.current_section = "images"
        self.reset_image_view()
        self.add_btn.setText("+ Image")
        self.note_title.hide()
        self.editor.hide()
        self.save_label.hide()

        self.gallery_scroll.show()
        self.preview_widget.hide()

        self.load_albums()

    def create_day_section(self, title):
        header = QLabel(title)
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.t};
                font-size: 18px;
                font-weight: bold;
                padding: 6px;
            }}
        """)
        
        flow_widget = QWidget()
        flow = FlowLayout(flow_widget, spacing=8)
        flow_widget.setLayout(flow)

        stretch_index = max(0, self.gallery_layout.count() - 1)
        self.gallery_layout.insertWidget(stretch_index, header)
        self.gallery_layout.insertWidget(stretch_index + 1, flow_widget)

        return flow

    def import_images(self):
        current = self.note_list.currentItem()
        if current is None:
            QMessageBox.information(
                self, "PassCore", "Please select an album first.!!"
            )
            return
        
        album_name = current.text()
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Images", str(Path.home() / "Pictures"), "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not files:
            return
        
        progress = QProgressDialog(
            "Importing Images to PassCore", None, 0, len(files), self
        )
        progress.setWindowTitle("PassCore Vault")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setCancelButton(None)

        for i ,file in enumerate(files, start=1):
            progress.setValue(i - 1)
            progress.setLabelText(f"Importing [{i}/{len(files)}]\n{Path(file).name}")
            QApplication.processEvents()
            import_image(Path(file), album_name, self.vault_key)
        
        progress.setValue(len(files))
        self.update_album_size(album_name)
        self.load_album(current)

    # Open selected images
    def open_selected_image(self, filename, album_name):
        pix = load_preview(self.vault_key, filename, album_name)
        self.image_preview.setPixmap(
            pix.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        with open(IMAGES_META, "r") as open_image:
            data = json.load(open_image)

        info = data["albums"][album_name][filename]

        self.preview_name.setText(f"Filename : {filename}")
        self.preview_size.setText(f"Size : {self.size_calc(info["size"])}")
        self.preview_resolution.setText(f"Dimension : {info["width"]}x{info["height"]}")
        self.preview_created.setText(f"Created : {info["created_at"]}")

        self.gallery_scroll.hide()
        self.preview_widget.show()
    
    # Load Albums into panel
    def load_albums(self):
        self.note_list.clear()
        if not IMAGES_META.exists():
            return
        
        with open(IMAGES_META, "r") as albums:
            l_albums = json.load(albums)
        
        for album_name in sorted(l_albums["albums"]):
            self.note_list.addItem(album_name)

        if self.note_list.count():
            self.note_list.setCurrentRow(0)

    # Load images inside albums (thumbnail)
    def load_album(self, item):
        self.clear_gallery()
        self.selected_images.clear()
        self.update_selection_label()

        album_name = item.text()
        self.update_album_size(album_name)

        with open(IMAGES_META, "r") as album:
            l_album = json.load(album)

        album = l_album["albums"][album_name]
        if not album:
            return

        timeline = defaultdict(list)
        for filename, info in album.items():
            created = datetime.strptime(info["created_at"], "%d-%m-%Y %I:%M:%S %p")
            day = created.strftime("%d %B %Y")
            timeline[day].append((created, filename))

        days = sorted(
            timeline.keys(), key=lambda d: datetime.strptime(d, "%d %B %Y"), reverse=True
        )
        today = datetime.today().date()

        for day in days:
            header_date = datetime.strptime(day, "%d %B %Y").date()
            images = sorted(timeline[day], reverse=True)
            if header_date == today:
                text = f"Today ({len(images)})"

            elif (today - header_date).days == 1:
                text = f"Yesterday ({len(images)})"

            else:
                text = f"{day} ({len(images)})"
            
            day_flow = self.create_day_section(text)

            for _, filename in images:
                pix = load_preview(self.vault_key, filename, album_name)
                if pix is None:
                    continue

                thumb = ImageLabel(filename, album_name)
                thumb.clicked.connect(self.open_selected_image)
                thumb.selectionChanged.connect(self.toggle_image_selection)
                thumb.contextRequested.connect(self.show_image_menu)
                thumb.setPixmap(
                    pix.scaledToHeight(
                    180, Qt.TransformationMode.SmoothTransformation
                    )
                )
                day_flow.addWidget(thumb)

    def toggle_image_selection(self, filename, album_name):
        key = (album_name, filename)
        if key in self.selected_images:
            self.selected_images.remove(key)
        else:
            self.selected_images.add(key)
        
        self.update_selection_label()
    
    def show_image_menu(self, filename, album_name, pos):
        menu = QMenu(self)
        delete = menu.addAction("Delete")
        rename = menu.addAction("Rename")

        chosen = menu.exec(pos)
        if chosen == delete:
            if self.selected_images:
                for album, image in list(self.selected_images):
                    self.delete_image(album, image)

                self.selected_images.clear()
                self.update_selection_label()

            else:
                reply = QMessageBox.question(
                    self, f"Delete Image", f"Are you sure?\nDelete {filename}?"
                )
                if reply != QMessageBox.Yes:
                    return

                self.delete_image(album_name, filename)
        
        elif chosen == rename:
            self.rename_image(album_name, filename)

    def update_album_size(self, album_name):
        if not IMAGES_META.exists():
            self.size_label.setText("Size\n0 Bytes")
            return

        with open(IMAGES_META, "r") as s:
            size_meta = json.load(s)

        album_size = size_meta["albums"].get(album_name, {})
        total_size = sum(
            image["size"]
            for image in album_size.values()
        )
        self.size_label.setText(f"Size:\n{self.size_calc(total_size)}")

    def update_selection_label(self):
        count = len(self.selected_images)
        if count == 0:
            self.selection_label.hide()
            return
        
        if count == 1:
            text = "1 Image Selected."
        else:
            text = f"{count} Images Selected..."
        
        self.selection_label.setText(text)
        self.selection_label.adjustSize()
        margin = 15
        
        self.selection_label.move(margin, self.gallery_scroll.height() - self.selection_label.height() - margin)
        self.selection_label.show()
        self.selection_label.raise_()

    def add_album(self):
        album_name, ok = QInputDialog.getText(
            self, "PassCore", "Album Name"
        )
        if not ok or not album_name.strip():
            return

        if not IMAGES_META.exists():
            data = {
                "albums": {}
            }
        else:
            with open(IMAGES_META, "r") as l_init:
                data = json.load(l_init)

        if album_name in data["albums"]: # Album already exists.?
            QMessageBox.information(
                self, "PassCore", "Album already exists."
            )
            return

        data["albums"][album_name] = {} # Create Empty Album.!
        with open(IMAGES_META, "w") as a_meta:
            json.dump(data, a_meta, indent=4)
        
        self.load_albums()

        items = self.note_list.findItems(album_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.note_list.setCurrentItem(items[0])

    def add_item(self):
        if self.current_section == "credentials":
            self.add_note()
        
        elif self.current_section == "images":
            if self.note_list.currentItem() is None:
                self.add_album()
            else:
                self.import_images()
    
    def rename_album(self, old_name):
        new_name, ok = QInputDialog.getText(
            self, "Rename Album", "New Name", text=old_name
        )
        if not ok or not new_name.strip():
            return

        with open(IMAGES_META, "r") as old_album:
            data = json.load(old_album)

        if new_name in data["albums"]:
            QMessageBox.information(self, "PassCore", "Album already exists.!")

        data["albums"][new_name] = data["albums"].pop(old_name)
        with open(IMAGES_META, "w") as r_album:
            json.dump(data, r_album, indent=4)

        self.load_albums()
        self.update_album_size(new_name)

    def delete_album(self, album):
        reply=QMessageBox.question(
            self,
            "Delete Album",
            f"Delete '{album}'?"
        )
        if reply!=QMessageBox.Yes:
            return

        with open(IMAGES_META,"r") as f:
            data=json.load(f)
        
        not_empty = data["albums"][album]
        if not_empty:
            QMessageBox.information(self, "PassCore Album", "Album has images.\ncannot be delete.!")
            return

        del data["albums"][album]
        with open(IMAGES_META,"w") as f:
            json.dump(data,f,indent=4)

        self.load_albums()
        self.clear_gallery()
        if self.note_list.count():
            self.note_list.setCurrentRow(0)

    def rename_image(self, album_name, filename):
        new_name, ok = QInputDialog.getText(
            self, "Rename Image", "New Image name: ", text=filename
        )
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        old_ext = Path(filename).suffix
        if Path(new_name).suffix == "":
            new_name += old_ext
        
        with open(IMAGES_META, "r") as name:
            r_name = json.load(name)
        
        album = r_name["albums"][album_name]
        if new_name!= filename and new_name in album:
            QMessageBox.warning(
                self, "PassCore", "Image name already exists."
            )
            return
        album[new_name] = album.pop(filename)
        image_info = album[new_name]

        # Modifies the image_index metadata.
        album[new_name]["filename"] = new_name
        album[new_name]["stem"] = Path(new_name).stem
        album[new_name]["extension"] = Path(new_name).suffix

        with open(IMAGES_META, "w") as modi_image:
            json.dump(r_name, modi_image, indent=4)

        # Modifies container metadata
        container_meta = Path(CONTAINER_DIR / image_info["uuid"] / "metadata.json")
        if container_meta.exists():
            with open(container_meta, "r") as ctn_data:
                ctn_meta = json.load(ctn_data)
            
            ctn_meta["filename"] = new_name
            ctn_meta["stem"] = Path(new_name).stem
            ctn_meta["extension"] = Path(new_name).suffix

            with open(container_meta, "w") as modi_ctn:
                json.dump(ctn_meta, modi_ctn,indent=4)
        
        current = self.note_list.currentItem() # Reload gallery.
        if current:
            self.load_album(current)
        
        QMessageBox.information(
        self, "PassCore", "Image renamed successfully."
        )

    def delete_image(self, album_name, filename):
        with open(IMAGES_META, "r") as del_img:
            selc_image = json.load(del_img)
        
        ctn_id = selc_image["albums"][album_name][filename]
        ctn_path = Path(CONTAINER_DIR / ctn_id["uuid"])
        
        secure_del_tree(ctn_path)
        
        del selc_image["albums"][album_name][filename]
        with open(IMAGES_META, "w") as del_img:
            json.dump(selc_image, del_img, indent=4)

        current = self.note_list.currentItem()
        if current:
            self.load_album(current)
        
        self.update_album_size(album_name)

    def clear_gallery(self):
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
            elif item.layout():
                while item.layout().count():
                        child = item.layout().takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

        self.gallery_layout.addStretch()
            
    def reset_image_view(self):
        # Leave image_preview mode.
        self.preview_widget.hide()
        self.gallery_scroll.hide()

        # Remove all thumbnails and clear the gallery along with the selection label.
        self.clear_gallery()
        self.selected_images.clear()
        self.update_selection_label()
        self.image_preview.clear()

        # Clear preview information.
        self.preview_name.clear()
        self.preview_size.clear()
        self.preview_resolution.clear()
        self.preview_created.clear()

    def show_documents(self):
        pass

    def show_audio(self):
        pass

    def show_videos(self):
        pass

    def show_favorites(self):
        pass

    def show_trash(self):
        pass
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        note_geo = self.note_list.geometry()
        self.update_selection_label()

        self.slide_menu.setGeometry(
            self.slide_menu.x(),
            note_geo.y(), # just below the menubar
            self.SLIDE_MENU_WIDTH, # Drawer width
            note_geo.height()
        )
        self.slide_menu.raise_()

    def slide_menu_items(self):
        self.slide_btn = []
        items = [
            ("🗝 Credentials", self.show_credentials),
            ("📷 Images", self.show_images),
            ("📄 Documents", self.show_documents),
            ("🎵 Audio", self.show_audio),
            ("🎬 Videos", self.show_videos),
            ("⭐ Favorites", self.show_favorites),
            ("🗑 Secure Trash", self.show_trash),
        ]
        for text, callback in items:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(callback)

            self.slide_btn.append(btn)
            self.slide_layout.addWidget(btn)

        self.slide_layout.addStretch()

    def toggle_slide_menu(self):
        self.slide_menu.raise_()
        y = self.menuBar().height()

        if self.menu_option:
            self.menu_animation.setStartValue(QPoint(0, y))
            self.menu_animation.setEndValue(QPoint(-self.SLIDE_MENU_WIDTH, y))
        
        else:
            self.menu_animation.setStartValue(QPoint(-self.SLIDE_MENU_WIDTH, y))
            self.menu_animation.setEndValue(QPoint(0, y))
        
        self.menu_animation.start()
        self.menu_option = not self.menu_option

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self.apply_capture_protection()

    def toggle_capture_protection(self, checked):
        self.settings["hide_from_capture"] = checked
        save_settings(self.settings)

        self.apply_capture_protection()

    def apply_capture_protection(self):
        """
            Enable or disable Windows screen capture protection.

            This prevents screenshots and most screen-recording applications
            from capturing the PassCore window on supported Windows versions.
        """

        if os.name != "nt":
            print("[PassCore] Screen capture protection is not supported on this platform.")
            return
        
        try:
            WDA_NONE = 0x00000000
            WDA_EXCLUDEFROMCAPTURE = 0x00000011

            hwnd = int(self.windowHandle().winId())

            affinity = (
                WDA_EXCLUDEFROMCAPTURE
                if self.settings.get("hide_from_capture", False)
                else WDA_NONE
            )

            success = ctypes.windll.user32.SetWindowDisplayAffinity(
                hwnd,
                affinity
            )

            if not success:
                error = ctypes.windll.kernel32.GetLastError()
                print(f"[PassCore] SetWindowDisplayAffinity failed (Error {error})")
                print("HWND:", hwnd)
                print("Affinity:", hex(affinity))
                print("Success:", success)
                print("LastError:", error)

        except Exception as e:
            print(f"[PassCore] Capture protection error: {e}")

    def update_welcome_label(self):
        self.welcome_label.setVisible(
            not self.editor.toPlainText().strip()
        )

    def add_note(self):
        if self.current_note >= 0:
            current = self.notes[self.current_note]

        if not current["content"].strip():
            QMessageBox.information(self, "PassCore", "Current note is empty.!")
            return
        
        self.notes.append({
            "title": "Untitled note",
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
        if self.current_section != "credentials":
            return

        if row < 0 or row >= len(self.notes):
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
                self, "PassCore Note", f"Are you sure?\n\nDelete: {self.notes[row]['title']}", QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            else:
                self.delete_note(row)

    def item_context_menu(self, pos):
        if self.current_section == "credentials":
            self.note_context_menu(pos)

        elif self.current_section == "images":
            self.album_context_menu(pos)

    def album_context_menu(self, pos):
        item = self.note_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        add = menu.addAction("Add Album")
        rename = menu.addAction("Rename Album")
        delete = menu.addAction("Delete Album")

        action = menu.exec(
            self.note_list.mapToGlobal(pos)
        )
        if action == add:
            self.add_album()

        elif action == rename:
            self.rename_album(item.text())

        elif action == delete:
            self.delete_album(item.text())

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
            self.editor.setExtraSelections([])

    def search_rec(self):        
        text = self.search_input.text().strip()
        if not text:
            self.matches = []
            self.current_match = -1
            self.match_label.setText("0 / 0")
            self.editor.setExtraSelections([])
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
        cursor = self.editor.textCursor()
        cursor.setPosition(self.matches[0])
        self.editor.setTextCursor(cursor)

        self.goto_match()
        self.match_label.setText(
            f"{self.current_match + 1}/{len(self.matches)}"
        )

    def goto_match(self):
        if not self.matches:
            self.editor.setExtraSelections([])
            return
        
        pos = self.matches[self.current_match]
        cursor = QTextCursor(self.editor.document())
        cursor.setPosition(pos)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            len(self.search_input.text())
        )
        selection = QTextEdit.ExtraSelection() # Highlight
        selection.cursor = cursor

        fmt = QTextCharFormat()
        fmt.setBackground(QColor(self.SEARCH_HIGHLIGHT))
        fmt.setForeground(QColor(self.w))
        selection.format = fmt

        self.editor.setExtraSelections([selection])
        scroll_cursor = self.editor.textCursor()
        scroll_cursor.setPosition(pos)
        self.editor.setTextCursor(scroll_cursor)
        self.editor.ensureCursorVisible()
        QApplication.processEvents()

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
class TimeLineLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)

        self.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px 4px;
            }
        """)
class ImageLabel(QLabel):
    clicked = Signal(str, str)
    selectionChanged = Signal(str, str)
    contextRequested = Signal(str, str, object)

    def __init__(self, filename, album_name, parent=None):
        super().__init__(parent)

        self.filename = filename
        self.album_name = album_name
        self.selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        if self.pixmap():
            return self.pixmap().size()

        return QSize(180, 180)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
                self.selected = not self.selected
                self.update_selection_style()

                self.selectionChanged.emit(self.filename, self.album_name)

            else:
                self.clicked.emit(self.filename, self.album_name)
        
        elif event.button() == Qt.MouseButton.RightButton:
            self.contextRequested.emit(self.filename, self.album_name, event.globalPos())
            

        super().mousePressEvent(event)

    def update_selection_style(self):
        if self.selected:
            self.setStyleSheet(f"""
                QLabel {{
                    border:3px solid #FFC107;
                    border-radius:8px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QLabel{
                    border:none;
                }
            """)

class ThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Theme")

        current_theme = (
            parent.settings["theme"]
            if parent
            else "default"
        )

        theme = THEMES[current_theme]
        w = theme["workspace"]
        i = theme["interactive"]
        t = theme["text"]

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {w};
            }}
            QLabel {{
                color: {t};
            }}
            QComboBox {{
                background-color: {i};
                color: {t};
                border: 2px solid {i};
                border-radius: 8px;
                padding: 6px;
            }}
            QPushButton {{
                background-color: {i};
                color: {t};

                border: 2px solid {i};
                border-radius: 8px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {w};
            }}
        """)

        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        label = QLabel("Choose a Theme")

        self.theme_combo = QComboBox()
        for theme_name in THEMES:
            self.theme_combo.addItem(
                theme_name.replace("_", " ").title(), theme_name
            )

        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("Apply")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(label)
        layout.addWidget(self.theme_combo)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

class PasswordDialog(QDialog):
    def __init__(self, title="PassCore Vault", confirm=False):
        super().__init__()
        self.settings = load_settings()
        self.apply_themes()
        self.confirm = confirm
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(resource_path("assets/PassCore.ico")))
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.w};
                color: {self.t};
            }}
            QLabel {{
                color: {self.t};
                background: transparent;
                border: none;
            }}
            QLineEdit {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.t};
            }}
            QCheckBox {{
                color: {self.t};
                background: transparent;
            }}
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

        # pAssCore logo
        logo = QLabel()
        pixmap = QPixmap(resource_path("assets/PassCore.png"))
        logo.setPixmap(pixmap.scaled(
            170, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))
        logo.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        title_label = QLabel("PassCore")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: bold;
                color: {self.t};
            }}
        """)
        description_label = QLabel(
            "PassCore is an offline-first password manager\n"
            "focused on local encrypted vault storage.\n\n"
            "Your data is secure.\n"
            "Your vault never leaves your device."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet(f"""
            QLabel {{
                font-size: 10pt;
                color: {self.t};
            }}
        """)

        info_layout = QVBoxLayout()
        info_layout.addWidget(title_label)
        info_layout.addWidget(description_label)
        info_layout.addStretch()

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addSpacing(10)
        header_layout.addLayout(info_layout)

        # Password fields
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Master Password"))
        form_layout.addWidget(self.password)
        if self.confirm:
            form_layout.addWidget(QLabel("Confirm Password"))
            form_layout.addWidget(self.confirm_password)
        
        form_layout.addWidget(self.show_pass)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.cancel_btn)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.setSpacing(5)
        layout.addLayout(form_layout)
        layout.addSpacing(5)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.setFixedSize(500,400)
    
    def apply_themes(self):
        theme = THEMES[self.settings["theme"]]

        self.win = theme["window"]
        self.w = theme["workspace"]
        self.i = theme["interactive"]
        self.b = theme["border"]
        self.t = theme["text"]

        self.lock_theme = BUTTONS["lock"]
        self.unlock_theme = BUTTONS["unlock"]
        self.save_theme = BUTTONS["save"]
        self.close_theme = BUTTONS["close"]
        
        self.STATUS_COLORS = {
            "locked": "#D4AF37",
            "unlocked": "#4CAF50",
            "corrupted": "#E53935"
        }

    def toggle_password(self, checked):
        mode = (QLineEdit.EchoMode.Normal
            if checked
            else QLineEdit.EchoMode.Password
        )
        self.password.setEchoMode(mode)
        
        if self.confirm:
            self.confirm_password.setEchoMode(mode)

    def validate_passwd(self):
        password = self.password.text().strip()
        if not password:
            QMessageBox.warning(
                self, "PassCore", "You forgot to type the password.!!\n\nMaster Password cannot be empty."
            )
            return
        
        if self.confirm:
            if (self.password.text() != self.confirm_password.text()):
                QMessageBox.warning(
                    self, "PassCore", "Password do not match.!\nPlease enter correct password... if you remember.! :_)*"
                )
                return
        self.accept()

    def closeEvent(self, event):
        self.reject()
        event.accept()

class PasswordGenerator(QDialog):
    def __init__(self, title="PassCore Password Generator"):
        super().__init__()
        self.settings = load_settings()
        self.apply_themes()
        self.setWindowTitle(title)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.w};
                color: {self.t};
            }}
            QLabel {{
                color: {self.t};
                font-size: 11pt;
                background: transparent;
            }}
            QLineEdit {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.t};
            }}
            QCheckBox {{
                color: {self.t};
                background: transparent;
            }}
            QPushButton {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.w};
                border: 2px solid {self.b};
            }}
            QPushButton:pressed {{
                background-color: {self.t};
                color: {self.w};
            }}
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

    def apply_themes(self):
        theme = THEMES[self.settings["theme"]]

        self.win = theme["window"]
        self.w = theme["workspace"]
        self.i = theme["interactive"]
        self.b = theme["border"]
        self.t = theme["text"]

        self.lock_theme = BUTTONS["lock"]
        self.unlock_theme = BUTTONS["unlock"]
        self.save_theme = BUTTONS["save"]
        self.close_theme = BUTTONS["close"]
        
        self.STATUS_COLORS = {
            "locked": "#D4AF37",
            "unlocked": "#4CAF50",
            "corrupted": "#E53935"
        }

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
        self.settings = load_settings()
        self.apply_themes()
        report = vault_health()
        self.setWindowTitle("Vault Health")
        self.setFixedSize(500, 550)

        score = report["score"]

        if score == 100:
            health = "🟢 HEALTHY"
            color = "#2E7D32"

        elif score >= 80:
            health = "🟡 WARNING"
            color = "#FBC02D"

        else:
            health = "🔴 CRITICAL"
            color = "#E53935"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.win};
            }}
            QFrame {{
                background-color: {self.i};
                border: 2px solid {self.b};
                border-radius: 8px;
            }}
            QLabel {{
                color: {self.t};
                border: none;
                background: transparent;
            }}
            QPushButton {{
                background-color: {self.i};
                color: {self.t};
                border: 2px solid {self.b};
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.w};
                border: 2px solid {self.b};
            }}
            QPushButton:pressed {{
                background-color: {self.t};
                color: {self.w};
            }}
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
        score_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16pt;
                font-weight: bold;
                color: {self.t};
            }}
        """)

        # ==========================================
        # Vault Information
        info_frame = QFrame()
        info_layout = QVBoxLayout()

        info_title = QLabel(
            "Vault Information"
        )
        info_title.setStyleSheet(f"""
            QLabel {{
                font-size: 13pt;
                font-weight: bold;
                color: {self.t};
            }}
        """)

        info_label = QLabel(f"""
            Created : {report['created']}
            Modified: {report['modified']}

            Blobs   : {report['blob_count']}
            Size    : {report['total_size']} bytes
            Backups : {report['backups']}
            """
        )
        info_label.setStyleSheet(f"""
            QLabel {{
                font-family: monospace;
                font-size: 11pt;
                color: {self.t};
            }}
        """)
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_label)

        info_frame.setLayout(info_layout)

        # ==========================================
        # Integrity Checks
        checks_frame = QFrame()
        checks_layout = QVBoxLayout()

        checks_title = QLabel("Integrity Checks")
        checks_title.setStyleSheet(f"""
            QLabel {{
                font-size: 13pt;
                font-weight: bold;
                color: {self.t};
            }}
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
                self.t
                if passed
                else "#C62828"
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
    
    def apply_themes(self):
        theme = THEMES[self.settings["theme"]]

        self.win = theme["window"]
        self.w = theme["workspace"]
        self.i = theme["interactive"]
        self.b = theme["border"]
        self.t = theme["text"]

        self.lock_theme = BUTTONS["lock"]
        self.unlock_theme = BUTTONS["unlock"]
        self.save_theme = BUTTONS["save"]
        self.close_theme = BUTTONS["close"]
        
        self.STATUS_COLORS = {
            "locked": "#D4AF37",
            "unlocked": "#4CAF50",
            "corrupted": "#E53935"
        }
    
    def refresh(self):
        self.close()
        dialog = VaultHealthDialog()
        dialog.exec()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassCoreUI()
    window.show()

    sys.exit(app.exec())
