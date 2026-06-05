# PassCore

A cryptographic password manager written in Python, focused on secure vault storage, authenticated encryption, and master-password-based access control.

> **Project Status:** Active Development (v1.1-core)

## Features

* AES-GCM authenticated encryption
* Argon2id-based key derivation
* Master password protected vault
* Random salt generation and persistence
* Binary vault storage
* Length-prefixed encrypted record format
* Vault lock/unlock workflow
* Save-before-exit protection
* First-run vault initialization
* Vault metadata management
* Blob-based encrypted storage architecture
* PySide6 graphical user interface

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

~/.local/share/passcore/
├── vault.salt
├── meta.json
├── blob_0000.bin
├── blob_0001.bin
└── ...

        ↓
Persistent Storage
```

Vault unlock flow:

```text
Encrypted Blobs
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

## Security Design

### Key Derivation

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

### Storage Layout

Linux systems use XDG-compliant storage locations:

```text
~/.local/share/passcore/
├── vault.salt
├── meta.json
├── blob_0000.bin
├── blob_0001.bin
└── ...

~/.cache/passcore/
└── passwords.bin (temporary)
```

The temporary working vault is reconstructed only when needed and is automatically removed after encryption and blob generation.

### Blob Architecture

Encrypted vault data is split into multiple binary blobs after encryption.

```text
  Encrypted Vault
        ↓
      Split
        ↓
   Blob Storage
```

During unlock:

```text
   Blob Storage
        ↓
     Rebuild
        ↓
  Encrypted Vault
        ↓
     Decrypt
```

The blob architecture is intended to reduce direct exposure of vault storage and provide a foundation for future distributed storage strategies.

## Current Capabilities

* Vault creation
* Vault initialization metadata
* Master password authentication
* Argon2id key derivation
* AES-GCM authenticated encryption
* Vault locking and unlocking
* Save vault contents
* Save-before-close workflow
* Automatic vault autosave
* Blob generation
* Blob reconstruction
* Temporary vault cleanup
* Wrong-password detection
* Corruption detection
* XDG-compliant storage layout
* Cross-platform path abstraction

## Planned Features

### Storage

* Distributed blob locations
* Automatic vault backups
* Vault export/import

### Security

* Blob integrity verification
* Secure overwrite before file deletion
* Optional memory-only reconstruction
* Vault health diagnostics

### User Experience

* Search records
* Record categories
* Password generator
* Auto-lock timer
* Cross-platform packaging

## Roadmap

* [x] AES-GCM encryption
* [x] Argon2id key derivation
* [x] Master password support
* [x] Binary vault format
* [x] Vault lock/unlock workflow
* [x] First-run initialization
* [x] Blob storage architecture
* [x] Blob reconstruction
* [x] Save-before-exit protection
* [x] Autosave workflow
* [x] XDG storage layout
* [x] Temporary vault cleanup
* [ ] Blob integrity verification
* [ ] Distributed blob storage
* [ ] Backup and recovery
* [ ] Password generator
* [ ] Auto-lock timer
* [ ] Cross-platform release


## Requirements

* Python 3.10+
* cryptography
* argon2-cffi
* PySide6

---

## Installation

```bash
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore

chmod +x run.sh
./run.sh # running bash will auto install the required dependencies 
```

---

## Project Structure

```text
~/.local/share/passcore/
├── vault.salt
├── meta.json
├── blob_0000.bin
├── blob_0001.bin
└── ...

~/.cache/passcore/
└── passwords.bin (temporary)
```

---

## Disclaimer

PassCore is an educational and experimental project.

It has not undergone a professional security audit and should not yet be considered production-ready for storing highly sensitive information.

While PassCore implements modern cryptographic primitives such as Argon2id and AES-GCM, users should review the source code carefully before relying on it for critical data protection.

