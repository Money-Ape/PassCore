# PassCore

![PassCore UI](assets/PassCoreUI_test01.png)

A cryptographic password manager written in Python, focused on secure vault storage, authenticated encryption, and master-password-based access control.

> **Project Status:** Alpha Pre-release (v0.2.0-alpha)

---

## Features

* AES-GCM authenticated encryption
* Argon2id-based key derivation
* Master password protected vault
* Random salt generation and persistence
* Binary vault storage
* Length-prefixed encrypted record format
* Vault lock/unlock workflow
* Save-before-exit protection
* Automatic vault autosave
* First-run vault initialization
* Vault metadata management
* Blob-based encrypted storage architecture
* Distributed blob container architecture
* Metadata-driven blob reconstruction
* SHA256 blob integrity verification
* Vault corruption detection
* Automatic backup creation
* Backup recovery system
* Backup retention management
* GUI-integrated recovery workflow
* Vault size tracking
* Vault created/modified tracking
* XDG-compliant storage layout
* Cross-platform path abstraction
* PySide6 graphical user interface

---

## Current Architecture

```text
  Master Password
        ↓
     Argon2id
        ↓
Vault Encryption Key
        ↓
     AES-GCM
        ↓
Temporary Working Vault
(passwords.bin)
        ↓
   Blob Splitting
        ↓
 Container Generation
        ↓

~/.local/share/passcore/
├── vault.salt
└── meta.json

~/.local/share/.passcore_db/
├── a76f1d9a4cd6493d/
│   └── blob_0000.bin
├── b371b06d00374fb6/
│   └── blob_0001.bin
├── e2e0f4c1dd31483c/
│   └── blob_0002.bin
└── ...

        ↓
Persistent Storage
```
flowchart LR

MasterPassword --> Argon2id
Argon2id --> AESGCM
AESGCM --> BlobStorage
BlobStorage --> IntegrityCheck
IntegrityCheck --> VaultEditor
---

## Vault Unlock Flow

```text
Encrypted Containers
        ↓
meta.json Verification
        ↓
 Verify Container
        ↓
Verify Blob Existence
        ↓
 Verify Blob Size
        ↓
  Verify SHA256
        ↓
Blob Reconstruction
        ↓
Temporary Working Vault
(passwords.bin)
        ↓
AES-GCM Decryption
        ↓
   Vault Editor
```

After encryption and blob generation, the temporary working vault is automatically removed from cache storage.

---

# Security Design

## Key Derivation

PassCore derives vault encryption keys from a master password using Argon2id.

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
```

---

## Storage Layout

PassCore uses platform-appropriate storage locations.

### Linux (XDG Compliant)

```text
~/.local/share/passcore/
├── vault.salt
└── meta.json

~/.local/share/.passcore_db/
├── container_id/
│   └── blob_*.bin

~/.cache/passcore/
└── passwords.bin (temporary)
```

### Windows

```text
%APPDATA%\PassCore\
├── vault.salt
└── meta.json

%LOCALAPPDATA%\PassCoreData\
├── container_id\
│   └── blob_*.bin

%LOCALAPPDATA%\PassCore\Cache\
└── passwords.bin (temporary)
```

The temporary working vault is reconstructed only when needed and is automatically removed after encryption and blob generation.

---

## Distributed Blob Storage

PassCore stores encrypted vault chunks inside randomized container directories.

Each blob receives a unique container identifier during encryption.

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

Container identifiers are recorded inside metadata and used during integrity verification and vault reconstruction.

Example metadata entry:

```json
{
    "blob_0000.bin": {
        "container": "a76f1d9a4cd6493d",
        "size": 32,
        "sha256": "..."
    }
}
```

This architecture separates:

```text
Storage Layer
        ↓
Metadata Layer
        ↓
Integrity Layer
        ↓
Recovery Layer
```

and provides a foundation for future distributed storage strategies.

---

## Blob Integrity Verification

Before vault reconstruction, PassCore validates stored blobs using metadata recorded in `meta.json`.

Verification includes:

* Container verification
* Blob existence verification
* Blob size verification
* SHA256 hash verification

Verification flow:

```text
    meta.json
        ↓
 Verify Container
        ↓
Verify Blob Existence
        ↓
  Verify Blob Size
        ↓
  Verify SHA256
        ↓
Blob Reconstruction
        ↓
Vault Decryption
```

This allows PassCore to distinguish between:

```text
Wrong Master Password
```

and

```text
Vault Corruption
```

before attempting decryption.

---

## Backup and Recovery

PassCore automatically creates compressed ZIP backups of vault storage data.

Backups contain:

* vault.salt
* meta.json
* All encrypted blob containers

Backups are stored separately from vault storage.

### Linux

```text
~/Documents/PassCore Backups/
```

### Windows

```text
Documents\PassCore Backups\
```

### Backup Workflow

```text
  Create Backup
        ↓
   ZIP Archive
        ↓
Backup Retention Check
        ↓
Keep Latest N Backups
```

### Recovery Workflow

```text
  Restore Backup
        ↓
 Extract Containers
        ↓
 Restore Metadata
        ↓
Integrity Verification
        ↓
   Vault Unlock
```

PassCore can recover from:

* Missing blobs
* Missing containers
* Corrupted blobs
* Accidental vault deletion
* Failed vault modifications

Backup retention automatically removes older backups after the configured limit is reached.

---

## Current Capabilities

### Vault Operations

* Vault creation
* Vault initialization metadata
* Master password authentication
* Vault locking and unlocking
* Save vault contents
* Save-before-close workflow
* Automatic vault autosave

### Cryptography

* Argon2id key derivation
* AES-GCM authenticated encryption
* Wrong-password detection

### Storage System

* Blob generation
* Blob reconstruction
* Distributed blob container storage
* Metadata-driven reconstruction
* Temporary vault cleanup
* Automatic backup creation
* Backup recovery
* Backup retention management
* XDG-compliant storage layout
* Cross-platform path abstraction

### Integrity Verification

* Corruption detection
* Container verification
* Blob existence verification
* Blob size verification
* SHA256 blob integrity verification

### User Interface

* PySide6 desktop application
* Vault status indicators
* Vault corruption indicators
* Save tracking
* Vault size tracking
* Created/modified timestamps
* Lock screen support
* Backup management menu
* Backend-integrated GUI

---

## Planned Features

### Storage

* Vault export/import

### Security

* Secure overwrite before file deletion
* Optional memory-only reconstruction
* Vault health diagnostics

### User Experience

* Search records
* Record categories
* Password generator
* Auto-lock timer
* Cross-platform packaging

---

## Roadmap

* [x] AES-GCM encryption
* [x] Argon2id key derivation
* [x] Master password support
* [x] Binary vault format
* [x] Vault lock/unlock workflow
* [x] First-run initialization
* [x] Blob storage architecture
* [x] Distributed blob storage
* [x] Blob reconstruction
* [x] Save-before-exit protection
* [x] Autosave workflow
* [x] XDG storage layout
* [x] Windows storage layout
* [x] Temporary vault cleanup
* [x] Blob integrity verification
* [x] Backup and recovery
* [x] Created/modified timestamps
* [x] PySide6 desktop interface
* [ ] Password generator
* [ ] Auto-lock timer
* [ ] Cross-platform packaging

---

## Platform Support

| Platform           | Status   |
| ------------------ | -------- |
| Linux (Arch Linux) | ✅ Tested |
| Windows 10         | ✅ Tested |
| Windows 11         | ✅ Tested |

---

## Requirements

* Python 3.10+
* cryptography
* argon2-cffi
* PySide6

---

## Installation

### Linux

```bash
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore

chmod +x run.sh
./run.sh
```

### Windows

```text
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore

Double-click windows.bat
```

The Windows launcher automatically:

* Creates a virtual environment (if missing)
* Installs required dependencies
* Launches PassCore

The Linux launcher performs equivalent dependency checks and initialization.

---

## Disclaimer

PassCore is an educational and experimental project.

It has not undergone a professional security audit and should not yet be considered production-ready for storing highly sensitive information.

While PassCore implements modern cryptographic primitives such as Argon2id and AES-GCM, users should review the source code carefully before relying on it for critical data protection.

---

## License

This project is currently released for educational and research purposes. Future licensing terms may evolve as the project matures.
