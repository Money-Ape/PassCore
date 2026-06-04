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
   passwords.bin
        ↓
   Blob Splitting
        ↓
vault/blob_0000.bin
vault/blob_0001.bin
vault/blob_0002.bin
        ↓
Persistent Storage
```

Vault unlock flow:

```text
Encrypted Blobs
        ↓
 Blob Reconstruction
        ↓
   passwords.bin
        ↓
 AES-GCM Decryption
        ↓
 Vault Editor
```

Encrypted records are stored as:

```text
[4-byte length]
[12-byte nonce]
[ciphertext + authentication tag]
```

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
* Vault locking and unlocking
* Save vault contents
* Save-before-close workflow
* Blob generation
* Blob reconstruction
* Corruption detection
* Wrong-password detection

## Planned Features

### Storage

* Distributed blob locations
* Hidden vault storage paths
* Automatic vault backups
* Vault export/import

### Security

* Blob integrity verification
* Secure deletion of temporary files
* Optional memory-only reconstruction
* Vault health diagnostics

### User Experience

* Search records
* Record categories
* Password generator
* Auto-lock timer
* Cross-platform packaging

## Requirements

* Python 3.10+
* cryptography
* argon2-cffi
* PySide6

Install dependencies:

```bash
chmod +x run.sh
./run.sh # dependencies will automatically installed by the script.!
```

## Installation

```bash
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore

chmod +x run.sh
./run.sh
```

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
* [ ] Blob integrity verification
* [ ] Distributed blob storage
* [ ] Backup and recovery
* [ ] Password generator
* [ ] Cross-platform release

## Disclaimer

PassCore is an educational and experimental project. It has not undergone professional security review and should not yet be considered production-ready for storing highly sensitive information.
