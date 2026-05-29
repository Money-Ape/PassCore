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
User Password Data
        ↓
Timestamp Processing
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

* Argon2
* scrypt
* PBKDF2

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
Temporary Working Data
        ↓
Change Detection
        ↓
   Re-Encrypt
        ↓
Delete Temporary Data on Shutdown
```

Additional work includes:

* Crash recovery
* Stale temporary file cleanup
* Reduced plaintext exposure
* In-memory processing

## Security Notes

PassCore is currently an experimental project and should not yet be considered production-ready.

Planned security improvements include:

* Master-password-based key derivation
* Improved vault integrity verification
* Secure temporary-file handling
* Enhanced record indexing
* In-memory vault operations

## Installation

```bash
git clone https://github.com/Money-Ape/PassCore.git
cd PassCore
python3 enc.py
```

## Requirements

* Python 3.10+
* cryptography

Install dependencies:

```bash
pip install cryptography
```

## Roadmap

* [x] AES-GCM encrypted records
* [x] Binary vault storage
* [x] Timestamp synchronization
* [x] Record update detection
* [ ] Master password support
* [ ] KDF integration (Argon2/scrypt/PBKDF2)
* [ ] Runtime vault workflow
* [ ] Crash-safe cleanup
* [ ] Memory-only vault processing
* [ ] Cross-platform release

## Disclaimer

PassCore is an educational and experimental project. Review the source code carefully before using it to store sensitive information.
