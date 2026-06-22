# PassCore Menu System

## Overview

PassCore provides a desktop interface built with PySide6 integrating vault management, diagnostics, backups, import/export tools, password generation, search, and theme management.

---

# File Menu

## Import Text File

Allows importing plaintext records into the current vault.

Workflow:

```text
Import TXT
      ↓
Replace Existing Notes
      OR
Append Notes
      ↓
Vault Editor
```

---

## Import PassCore Vault (.pcv)

Imports a previously exported PassCore vault.

Workflow:

```text
Select Vault
      ↓
Extract Archive
      ↓
Restore Metadata
      ↓
Restore Containers
      ↓
Lock Imported Vault
      ↓
Unlock Vault
```

---

## Export PassCore Vault (.pcv)

Creates a portable encrypted PassCore vault archive.

Archive Contents:

* vault.salt
* meta.json
* encrypted containers

---

## Settings

```text
Settings
├── Auto Lock
└── Themes
```

---

### Auto Lock

Configure automatic vault locking after inactivity.

Available:

* 1 minute
* 5 minutes
* 10 minutes
* 30 minutes
* 60 minutes

---

### Themes

PassCore includes 13 built-in themes.

Available Themes:

* Default
* Slate Grey
* Pale Green
* Beige
* Mint Green
* Sage Green
* Light Blue
* Blue Grey
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

# Tools Menu

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
* Backup Management
* Import TXT
* Import PCV
* Export PCV
* Settings System
* Welcome Screen
* Live Theme Switching

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
