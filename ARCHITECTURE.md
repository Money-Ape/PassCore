# PassCore Architecture

```mermaid
flowchart TD

%% ==========================================================
%% ENCRYPTION & STORAGE FLOW
%% ==========================================================

MP["Master Password"]
A["Argon2id Key Derivation"]
K["Vault Encryption Key"]
E["AES-GCM Encryption"]
RAM1["Encrypted Bytes (RAM)"]
B["Blob Splitting"]
C["Container Generation"]

MP --> A
A --> K
K --> E
E --> RAM1
RAM1 --> B
B --> C

%% ==========================================================
%% DISTRIBUTED BLOB STORAGE
%% ==========================================================

META["meta.json"]

C --> D1["container_id/blob_0000.bin"]
C --> D2["container_id/blob_0001.bin"]
C --> D3["container_id/blob_0002.bin"]
C --> D4["..."]

META -. Metadata Mapping .-> D1
META -. Metadata Mapping .-> D2
META -. Metadata Mapping .-> D3
META -. Metadata Mapping .-> D4

%% ==========================================================
%% INTEGRITY VERIFICATION
%% ==========================================================

VM["Verify Metadata"]
VC["Verify Container"]
VE["Verify Blob Existence"]
VS["Verify Blob Size"]
VH["Verify SHA256 Hash"]

META --> VM

D1 --> VC
D2 --> VC
D3 --> VC
D4 --> VC

VM --> VC
VC --> VE
VE --> VS
VS --> VH

%% ==========================================================
%% RECONSTRUCTION
%% ==========================================================

BR["Blob Reconstruction"]
RAM2["Encrypted Bytes (RAM)"]
DEC["AES-GCM Decryption"]
EDITOR["Vault Editor"]

VH --> BR
BR --> RAM2
RAM2 --> DEC
DEC --> EDITOR

%% ==========================================================
%% UI LAYER
%% ==========================================================

EDITOR --> THEME
THEME["Theme Engine"]
THEME --> UI["PassCore UI"]

%% ==========================================================
%% BACKUP SYSTEM
%% ==========================================================

BACKUP["Backup System"]

BR --> BACKUP
BACKUP --> ZIP["ZIP Archive"]
ZIP --> RETENTION["Backup Retention"]
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

# Distributed Blob Storage

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
meta.json
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
meta.json
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

# Backup Architecture

Backups contain:

* vault.salt
* meta.json
* encrypted containers

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
settings.json
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
└── meta.json

~/.local/share/.passcore_db/
├── container_id/
│   └── blob_*.bin
```

## Windows

```text
%APPDATA%\PassCore\
├── vault.salt
└── meta.json

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
Vault Editor Layer
        ↓
Cryptography Layer
        ↓
Storage Layer
        ↓
Integrity Layer
        ↓
Backup Layer
```

PassCore separates storage, integrity verification, encryption, backups, and user interaction into independent layers to simplify future development and maintenance.
