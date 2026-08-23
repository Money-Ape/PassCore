# PassCore Architecture
This Document describes the internal architecture of PassCore, including encryption, blob storage, integrity verification, image storage, backups, and the desktop application workflow.

```mermaid
flowchart TD

%% ==========================================================
%% AUTHENTICATION
%% ==========================================================

MP["Master Password"]
KDF["Argon2id KDF"]
KEY["256-bit Vault Key"]

MP --> KDF
KDF --> KEY


%% ==========================================================
%% APPLICATION LAYER
%% ==========================================================

subgraph PY["Python Application Layer"]

    APP["PassCore Application"]

    EDITOR["Vault Editor"]
    GALLERY["Image Gallery"]

    ENC["AES-GCM Encryption"]
    DEC["AES-GCM Decryption"]

    CACHE["Thumbnail Cache"]
    PREVIEW["Image Preview"]

    THEME["Theme Engine"]
    UI["PySide6 UI"]

    APP --> EDITOR
    APP --> GALLERY

    EDITOR --> ENC
    GALLERY --> ENC

    DEC --> EDITOR
    DEC --> GALLERY

    GALLERY --> CACHE
    CACHE --> PREVIEW

    EDITOR --> THEME
    PREVIEW --> THEME
    THEME --> UI

end


%% ==========================================================
%% CRYPTOGRAPHY
%% ==========================================================

KEY --> ENC
ENC --> RAM1["Encrypted Bytes (RAM)"]

RAM1 --> SPLIT["Blob Splitting"]

SPLIT --> NOTEUUID["Note / Image UUID"]

KEY --> DEC

NOTEUUID --> RECONSTRUCT["Blob Reconstruction"]

RECONSTRUCT --> RAM2["Encrypted Bytes (RAM)"]

RAM2 --> DEC


%% ==========================================================
%% NOTE STORAGE
%% ==========================================================

subgraph STORAGE["Encrypted Vault Storage"]

    META["metadata.json"]

    C1["Container UUID"]
    C2["Container UUID"]
    C3["Container UUID"]

    B1["blob_0000.bin"]
    B2["blob_0001.bin"]
    B3["blob_0002.bin"]
    B4["blob_0003.bin"]
    BN["..."]

    NOTEUUID --> META

    META --> C1
    META --> C2
    META --> C3

    C1 --> B1
    C1 --> B2

    C2 --> B3
    C2 --> B4

    C3 --> BN

end


%% ==========================================================
%% GLOBAL INDEXES
%% ==========================================================

INDEX["notes_index.json"]
IMGINDEX["images_index.json"]

INDEX --> NOTEUUID
IMGINDEX --> NOTEUUID


%% ==========================================================
%% VAULT FILES
%% ==========================================================

SALT["vault.salt"]
SETTINGS["settings.yaml"]

SALT --> KDF


%% ==========================================================
%% PYTHON ↔ C# BRIDGE
%% ==========================================================

subgraph BRIDGE["Python ↔ C# Utility Bridge"]

    PYUTIL["passcore_util.py"]

    JSONREQ["JSON Request"]
    JSONRES["JSON Response"]

    PYUTIL --> JSONREQ
    JSONRES --> PYUTIL

end


%% ==========================================================
%% C# UTILITY ENGINE
%% ==========================================================

subgraph CS["PassCore.Utilities — C#"]

    DISPATCH["Program.cs\nOperation Dispatcher"]

    BACKUP["BackupService"]
    PCV["VaultFileService"]
    HEALTH["HealthService"]

    DEL["DeleteDirectoryContents"]
    FILEUTIL["File Utilities"]

    DISPATCH --> BACKUP
    DISPATCH --> PCV
    DISPATCH --> HEALTH

    PCV --> DEL
    PCV --> FILEUTIL

end


%% ==========================================================
%% C# OPERATIONS
%% ==========================================================

JSONREQ --> DISPATCH
DISPATCH --> JSONRES

BACKUP --> ZIP["Backup ZIP Archive"]
ZIP --> RETENTION["Retention Policy\nMax 10 Backups"]

PCV --> PCVFILE[".pcv Archive"]

HEALTH --> VERIFY["Integrity Verification"]


%% ==========================================================
%% BACKUP INPUTS
%% ==========================================================

INDEX --> BACKUP
IMGINDEX --> BACKUP
META --> BACKUP
SALT --> BACKUP
SETTINGS --> BACKUP
B1 --> BACKUP
B2 --> BACKUP
B3 --> BACKUP
B4 --> BACKUP
BN --> BACKUP


%% ==========================================================
%% PCV EXPORT / IMPORT
%% ==========================================================

INDEX --> PCV
IMGINDEX --> PCV
META --> PCV
SALT --> PCV
SETTINGS --> PCV

PCVFILE --> PCV


%% ==========================================================
%% HEALTH CHECKS
%% ==========================================================

INDEX --> HEALTH
IMGINDEX --> HEALTH
META --> HEALTH

VERIFY --> VC["Verify Containers"]
VC --> VE["Verify Blob Existence"]
VE --> VS["Verify Blob Size"]
VS --> VH["Verify SHA-256"]


%% ==========================================================
%% RECONSTRUCTION
%% ==========================================================

VH --> RECONSTRUCT


%% ==========================================================
%% UI → UTILITY OPERATIONS
%% ==========================================================

UI --> PYUTIL

PYUTIL -->|"vault_health"| HEALTH
PYUTIL -->|"images_health"| HEALTH

PYUTIL -->|"backup_mark_changed"| BACKUP
PYUTIL -->|"backup_create"| BACKUP
PYUTIL -->|"backup_restore"| BACKUP

PYUTIL -->|"vault_export"| PCV
PYUTIL -->|"vault_import"| PCV
```

---

# Encryption Workflow

```text
Master Password
        ↓
      Salt
        ↓
    Argon2id
        ↓
256-bit Vault Key
        ↓
     AES-GCM
        ↓
 Encrypted Vault Data
```

PassCore derives encryption keys from a user-supplied master password using Argon2id.

The derived key is used with AES-GCM authenticated encryption.

---

# Blob Storage Architecture

PassCore stores encrypted vault data inside distributed container directories.

Example:

```text
.passcore_db/

├── a76f1d9a4cd6493d/
│   └── blob_0000.bin

├── b371b06d00374fb6/
│   └── blob_0001.bin

├── e2e0f4c1dd31483c/
│   └── blob_0002.bin
```

Each blob receives:

* Container ID
* File Size
* SHA256 Hash

Metadata is recorded inside:

```text
notes_index.json
```

---

# Integrity Verification

Before vault reconstruction, PassCore validates:

* Metadata
* Containers
* Blob existence
* Blob size
* SHA256 hashes

Workflow:

```text
notes_index.json
      ↓
Verify Metadata
      ↓
Verify Container
      ↓
Verify Blob Existence
      ↓
Verify Blob Size
      ↓
Verify SHA256
      ↓
Vault Reconstruction
```

This allows PassCore to distinguish between:

```text
Wrong Password
```

and

```text
Vault Corruption
```

before decryption occurs.

---

# In-Memory Processing

PassCore processes vault data entirely in memory.

```text
Encrypted Containers
        ↓
Integrity Verification
        ↓
Blob Reconstruction
        ↓
Encrypted Bytes (RAM)
        ↓
AES-GCM Decryption
        ↓
Vault Editor
        ↓
AES-GCM Encryption
        ↓
Encrypted Bytes (RAM)
        ↓
Blob Splitting
        ↓
Encrypted Containers
```

No temporary vault files are created during normal operation.

---

# Image Vault Architecture

Imported images follow the same secure storage pipeline as the vault.

```text
    Image File
        ↓
   Read Bytes
        ↓
 AES-GCM Encryption
        ↓
Encrypted Image Bytes
        ↓
  Blob Splitting
        ↓
Random Container Allocation
        ↓
  metadata.json
        ↓
 images_index.json
```

When an image is opened:

```text
  images_index.json
        ↓
   Locate Image
        ↓
Integrity Verification
        ↓
 Blob Reconstruction
        ↓
Encrypted Image Bytes (RAM)
        ↓
 AES-GCM Decryption
        ↓
   Image Preview
```

Image data is reconstructed entirely in memory. No temporary decrypted image files are written to disk.

---

# Thumbnail Cache

To improve gallery performance, PassCore caches recently reconstructed image previews in memory.

```text
 Open Image
      ↓
 Cache Lookup
      ↓
Cache Hit ─────► Display Thumbnail
      │
      ▼
 Cache Miss
      ↓
Blob Reconstruction
      ↓
AES-GCM Decryption
      ↓
Generate Thumbnail
      ↓
Store in Cache
      ↓
Display Thumbnail
```

The cache avoids repeated blob reconstruction and decryption while browsing albums.

---

# Backup Architecture

Backups contain:

* vault.salt
* notes_index.json
* images_index.json
* settings.yaml
* encrypted blob containers

Workflow:

```text
Create Backup
      ↓
ZIP Archive
      ↓
Backup Retention Check
      ↓
Store Backup
```

Recovery:

```text
Restore Backup
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

---

# Theme Engine

PassCore includes a runtime theme engine.

Theme settings are stored in:

```text
settings.yaml
```

Workflow:

```text
Select Theme
      ↓
Save Settings
      ↓
refresh_theme()
      ↓
Apply UI Styles
```

Theme changes are applied immediately without restarting the application.

---

# Storage Layout

## Linux

```text
~/.local/share/passcore/
├── vault.salt
└── notes_index.json

~/.local/share/.passcore_db/
├── container_id/
│   └── blob_*.bin
```

## Windows

```text
%APPDATA%\PassCore\
├── vault.salt
└── notes_index.json

%LOCALAPPDATA%\PassCoreData\
├── container_id\
│   └── blob_*.bin
```

---

# Packaging

## Debian

```text
/usr/bin/passcore_amd64
/usr/share/applications/passcore.desktop
/usr/share/pixmaps/passcore.png
```

## Arch Linux

```text
/usr/bin/passcore
/usr/share/applications/passcore.desktop
/usr/share/pixmaps/passcore.png
```

---

# Architecture Layers

```text
User Interface Layer
        ↓
    Theme Layer
        ↓
Vault Editor / Gallery Layer
        ↓
 Cryptography Layer
        ↓
Storage & Metadata Layer
        ↓
Integrity & Health Layer
        ↓
Python ↔ C# Utility Bridge
        ↓
C# Utility Layer
        ├── Backup / Restore
        ├── PCV Import / Export
        └── Vault Health
```

PassCore separates storage, integrity verification, encryption, backups, and user interaction into independent layers to simplify future development and maintenance.