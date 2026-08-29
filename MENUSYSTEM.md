# PassCore Menu System

## Overview

PassCore provides a desktop interface built with PySide6 integrating vault management, diagnostics, backups, import/export tools, password generation, search, and theme management.

The menu bar's top-right corner also carries a "☰" toggle button that opens/closes a slide-out sidebar menu alongside the standard File/Edit/View/Tools menus.

---

# File Menu

## Import / Export

Opens the **Import / Export** dialog — a single tabbed window (Import / Export) covering both Credentials and Images. The vault must be unlocked; selecting this item while locked shows a prompt instead of opening the dialog.

This dialog operates on portable **PassCore Package** files (`.pcx`), which are separate from the full-vault `.pcv` backup format described in [ARCHITECTURE.md](ARCHITECTURE.md#pcv-export--import). A `.pcx` package holds a hand-picked set of credentials or image albums — not the whole vault — and is protected by its own package password (independent of the vault's master password), derived with Argon2id and sealed with AES-GCM.

### Import Tab

**Import as:** `Credentials` or `Images`. The available source options change based on this selection:

| Import as | Available Sources |
|---|---|
| Credentials | Import Text (`.txt`), Import PassCore Package (`.pcx`) |
| Images | Import PassCore Package (`.pcx`) |

Every package is type-checked before anything is written: a package's embedded manifest type must match the currently selected "Import as" type, or the import is rejected outright (a Credentials package cannot be dropped into Images, and vice versa).

**Import Text** workflow:

```text
Select .txt File
      ↓
Read File
      ↓
Validate / Convert (secure YAML check)
      ↓
Append as New Note
      ↓
Save Vault
```

**Import PassCore Package** workflow:

```text
Select .pcx File
      ↓
Enter Package Password
      ↓
Decrypt Package (Argon2id + AES-GCM)
      ↓
Verify Manifest Type Matches Selection
      ↓
Extract Items
      ↓
Credentials → Append Notes (auto-renamed on title collision)
      OR
Images → Import Albums / Images
      ↓
Save Vault / Refresh Gallery
```

---

### Export Tab

**Export:** `Credentials` or `Images`. The list below shows every note (Credentials) or every album (Images) currently in the vault, each with its own checkbox, alongside **Select All** / **Clear All** buttons and a live "N selected" counter.

Exporting requires choosing a package password, which is used to encrypt the resulting `.pcx` file — this password is separate from, and does not need to match, the vault's master password.

**Export Selected** workflow:

```text
Select Credentials or Images
      ↓
Check Items to Export
      ↓
Choose Package Password
      ↓
Decrypt Selected Items In-Memory
      ↓
Build Manifest + Payload Files
      ↓
Compress to Inner Archive
      ↓
Encrypt (Argon2id + AES-GCM)
      ↓
Save .pcx File
```

`.pcx` Package Contents (inside the encrypted, zipped archive):

* `manifest.json` — package type (`credentials` or `images`), creation timestamp, and an index of included items
* Credentials: one JSON file per note (`notes/0000.json`, `notes/0001.json`, …) containing title, content, and export timestamp
* Images: one file per image, grouped by album (`images/0000/0000_photo.png`, …), plus per-image metadata (filename, extension, dimensions, MIME type) in the manifest

---

# Edit Menu

## Search Records

Search records stored in the vault.

Features:

* Ctrl + F shortcut
* Match highlighting
* Previous / Next navigation
* Match counter
* Case-insensitive search

Workflow:

```text
Enter Search Term
        ↓
Locate Matches
        ↓
Navigate Results
```

---

## Settings

```text
Edit
└── Settings
    ├── Auto-Lock Timer
    ├── Theme
    └── Hide from Screen Capture/Recording (Windows only)
```

---

### Auto-Lock Timer

Configure automatic vault locking after inactivity.

Available:

* 1 minute
* 5 minutes
* 10 minutes
* 30 minutes
* 60 minutes

---

### Theme

PassCore includes 16 built-in themes.

Available Themes:

* Default
* Cozy Pink
* Soft Blossom
* Catppuccin
* Slate Grey
* Forest
* Beige
* Mint Green
* Sage Green
* Tokyo Night
* Nord
* Ivory
* Cream Dark Grey
* Sage Dark Grey
* Blue Grey Black
* Charcoal

Theme changes apply instantly.

Workflow:

```text
Open Theme Dialog
      ↓
Select Theme
      ↓
Apply Theme
      ↓
refresh_theme()
      ↓
Updated Interface
```

---

### Hide from Screen Capture/Recording (Windows only)

A checkable toggle that prevents the PassCore window from appearing in screen captures or recordings.

* Windows-only — the action is disabled (greyed out) on non-Windows platforms.
* Reflects and updates the `hide_from_capture` setting.
* Toggling it applies/removes capture protection immediately for the current session.

---

# View Menu

## Open Backup Folder

Opens the platform's local backup directory in the system file browser, for direct access to stored backup archives.

Access:

```text
View
└── Open Backup Folder
```

---

# Tools Menu

## Create Backup

Manually triggers an on-demand vault backup, independent of the automatic backup created after autosave.

Access:

```text
Tools
└── Create Backup
```

---

## Restore Backup

Restores the vault from a previously created backup archive.

Workflow:

```text
Select Backup
      ↓
Extract Archive
      ↓
Restore Metadata
      ↓
Restore Containers
      ↓
Integrity Verification
      ↓
Vault Unlock
```

Access:

```text
Tools
└── Restore Backup
```

---

## Password Generator

Generate cryptographically secure passwords.

Features:

* Configurable length
* Uppercase letters
* Lowercase letters
* Numbers
* Symbols

Access:

```text
Tools
└── Password Generator
```

---

## Vault Health

Vault Health provides diagnostics and integrity reporting.

Reports:

* Vault Health Score
* Metadata Status
* Container Status
* Blob Status
* Blob Size Status
* SHA256 Verification
* Backup Availability
* Vault Statistics

Access:

```text
Tools
└── Vault Health
```

---

# Vault Operations

## Unlock Vault

```text
Master Password
      ↓
Argon2id
      ↓
Integrity Verification
      ↓
Vault Reconstruction
      ↓
Vault Editor
```

---

## Lock Vault

```text
Lock Request
      ↓
Remove Key From Memory
      ↓
Display Lock Screen
      ↓
Vault Locked
```

---

## Auto Lock

```text
User Inactive
      ↓
Timer Expired
      ↓
Vault Locked
```

---

## Autosave

```text
Editor Modified
      ↓
Autosave Delay
      ↓
Save Vault
      ↓
Create Backup
```

---

# Welcome Screen

PassCore displays a placeholder-style welcome screen when notes are empty.

Features:

* Not stored inside vault data
* Not encrypted
* Not saved
* Automatically hides when user starts typing
* Reappears when editor becomes empty

Workflow:

```text
Empty Note
      ↓
Show Welcome Screen
      ↓
User Types
      ↓
Hide Welcome Screen
```

---

# Current Interface Features

* Vault Lock / Unlock
* Auto Lock Timer
* Autosave
* Save Tracking
* Vault Size Tracking
* Created / Modified Tracking
* Vault Status Monitoring
* Search Records
* Password Generator
* Vault Health Diagnostics
* Theme Manager
* Manual & Automatic Backup Creation
* Backup Restoration
* Open Backup Folder
* Screen Capture Protection (Windows only)
* Import / Export Dialog (Text, PassCore Package `.pcx` — Credentials & Images)
* Settings System
* Welcome Screen
* Live Theme Switching
* Slide-out Menu (☰)

---

# Keyboard Shortcuts

| Shortcut | Action         |
| -------- | -------------- |
| Ctrl + F | Search Records |
| Ctrl + S | Save Vault     |
| Ctrl + L | Lock Vault     |

---

# User Interface Components

## Sidebar

* Note Management
* Search Navigation
* Vault Statistics

## Editor

* Multi-note editing
* Autosave integration
* Welcome screen overlay

## Status Area

Displays:

* Vault Status
* Last Save Time
* Vault Size

## Dialogs

* Password Dialog
* Theme Dialog
* Password Generator
* Vault Health
* Search Interface

---

PassCore's interface is designed to provide quick access to vault operations while maintaining a simple and secure workflow.