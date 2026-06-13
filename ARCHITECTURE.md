## PassCore Architecture

```mermaid
flowchart TD

%% ==========================================================
%% ENCRYPTION & STORAGE FLOW
%% ==========================================================

MP["Master Password"]
A["Argon2id Key Derivation"]
K["Vault Encryption Key"]
E["AES-GCM Encryption"]
W["Temporary Working Vault<br/>passwords.bin"]
B["Blob Splitting"]
C["Container Generation"]

MP --> A
A --> K
K --> E
E --> W
W --> B
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
DEC["AES-GCM Decryption"]
EDITOR["Vault Editor"]

VH --> BR
BR --> DEC
DEC --> EDITOR

%% ==========================================================
%% STORAGE LOCATIONS
%% ==========================================================

SYS["Storage Locations"]

BR --> SYS

SYS --> LINUX
SYS --> WINDOWS

subgraph LINUX["Linux Storage Layout"]
    LNX["XDG-Compliant Storage"]
end

subgraph WINDOWS["Windows Storage Layout"]
    WIN["Windows Storage Layout"]
end

%% ==========================================================
%% RECOVERY FLOW
%% ==========================================================

subgraph RECOVERY["Recovery Flow (Backup Restore)"]

R1["Restore Backup"]
R2["Extract Backup"]
R3["Restore Metadata"]
R4["Restore Containers"]
R5["Integrity Verification"]
R6["Vault Unlock"]

R1 --> R2
R2 --> R3
R3 --> R4
R4 --> R5
R5 --> R6

end
```

---

## Linux Storage Layout

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

---

## Windows Storage Layout

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

---

## Recovery Flow

```text
Restore Backup
      ↓
Extract Backup
      ↓
Restore Metadata
      ↓
Restore Containers
      ↓
Integrity Verification
      ↓
Vault Unlock
```