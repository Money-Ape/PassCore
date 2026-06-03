# PassCore

A cryptographic password manager written in Python, focused on secure vault storage, encrypted record management, and timestamp-based change tracking.

> **Project Status:** Active Development

## Features

* AES-GCM encryption for password records
* Per-record random nonce generation
* Binary vault storage
* Timestamp tracking for password entries
* Detection of modified records
* Import and synchronization from plaintext sources
* Length-prefixed encrypted record format
* Python-based implementation with minimal dependencies

## Current Architecture

```text
Decrypt Password Data
        ↓
Editor for User to modify
        ↓
Encrypted Record Generation
        ↓
Binary Vault Storage
```

Encrypted records are stored as:

```text
[4-byte length]
[12-byte nonce]
[ciphertext + authentication tag]
```

## Planned Features

### Vault Key Derivation

Replace persistent raw encryption keys with keys derived from a master password using a Key Derivation Function (KDF):

* Argon2 [argon2id]
* scrypt
* AESGCM

Planned flow:

```text
Master Password
        ↓
       KDF
        ↓
Vault Encryption Key
        ↓
AES-GCM Encryption
```

### Runtime Working Vault

Future versions are planned to use a temporary runtime working file:

```text
Encrypted Vault
        ↓
Decrypt on Startup
        ↓
Editor for User to modify
        ↓
Change Detection with diff
        ↓
   Re-Encrypt
        ↓
Binary chunks local-storage
```

Additional work includes:

* Crash recovery - *solved*
* Stale temporary file cleanup - *solved*
* Reduced plaintext exposure
* In-memory processing - *solved*

## Security Notes

PassCore is currently an experimental project and should not yet be considered production-ready.

Planned security improvements include:

* Improved vault integrity verification
* Enhanced record indexing

## Requirements

* Python 3.10+
* cryptography
* python-argon2

Install dependencies:

```bash
./run.sh # to install all dependencies
```

## Installation

```bash
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore
chmod +x run.sh
./run.sh
```

## Roadmap

* [x] AES-GCM encrypted records
* [x] Binary vault storage
* [ ] Timestamp synchronization
* [x] Record update detection
* [x] Master password support
* [x] KDF integration (Argon2/scrypt/PBKDF2)
* [x] Runtime vault workflow
* [x] Crash-safe cleanup
* [x] Memory-only vault processing
* [ ] Cross-platform release

## Disclaimer

PassCore is an educational and experimental project. Review the source code carefully before using it to store sensitive information.
