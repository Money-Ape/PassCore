import json, hashlib, os, platform
from pathlib import Path
from backup import META_FILE, BACKUP_ROOT

def sha256_blob(shafile_path):
    hh = hashlib.sha256() # hash helper to cross check modifixation of any blobs

    with open(shafile_path, "rb") as bsha:
        while chunk := bsha.read(8192): # Read 8KB at a time 
            hh.update(chunk)

    return hh.hexdigest() # return hexadecimal hash string.!

def _iter_notes(meta):
    # notes_index.json shape
    for title, note in meta["notes"].items():
        note_id = next(iter(note))
        yield title, note_id

def get_notes_container_dir():
    sys = platform.system()
    if sys == "Linux":
        return Path.home() / ".local" / "share" / ".passcore_db" / "notes"

    elif sys == "Windows":
        return Path(os.getenv("LOCALAPPDATA")) / "PassCoreData" / "notes"
    else:
        raise RuntimeError(f"Unsupported OS: {sys}")

CONTAINER_DIR = get_notes_container_dir()

def _load_note_meta(note_id):
    note_dir = CONTAINER_DIR / note_id
    meta_path = note_dir / "metadata.json"
    with open(meta_path, "r") as f:
        return note_dir, json.load(f)

def verify_metadata():
    try:
        with open(META_FILE, "r") as vmeta:
            meta = json.load(vmeta)

        if "notes" not in meta:
            return False

        for title, note in meta["notes"].items():
            note_id = next(iter(note))
            required = ["created", "modified"]
            if not all(key in note[note_id] for key in required):
                return False

        return True

    except Exception:
        return False

def verify_containers(meta):
    for title, note_id in _iter_notes(meta):
        note_dir = CONTAINER_DIR / note_id
        if not note_dir.exists() or not (note_dir / "metadata.json").exists():
            return False

    return True

def verify_blob_existence(meta):
    for title, note_id in _iter_notes(meta):
        try:
            note_dir, note_meta = _load_note_meta(note_id)
        except Exception:
            return False

        for blob_name, info in note_meta["blobs"].items():
            blob_path = note_dir / info["container"] / blob_name
            if not blob_path.exists():
                return False

    return True

def verify_blob_size(meta):
    for title, note_id in _iter_notes(meta):
        try:
            note_dir, note_meta = _load_note_meta(note_id)

        except Exception:
            return False

        for blob_name, info in note_meta["blobs"].items():
            blob_path = note_dir / info["container"] / blob_name
            if not blob_path.exists() or blob_path.stat().st_size != info["size"]:
                return False

    return True

def verify_sha256(meta):
    for title, note_id in _iter_notes(meta):
        try:
            note_dir, note_meta = _load_note_meta(note_id)

        except Exception:
            return False

        for blob_name, info in note_meta["blobs"].items():
            blob_path = note_dir / info["container"] / blob_name
            if not blob_path.exists():
                return False

            current_hash = sha256_blob(blob_path)
            if current_hash != info["sha256"]:
                return False

    return True

def count_backup():
    if not BACKUP_ROOT.exists():
        return False

    return len(list(BACKUP_ROOT.glob("*.zip")))

def calc_score(metadata_ok, containers_ok, existence_ok, size_ok, sha256_ok):
    score = 0

    if metadata_ok:
        score += 20
    if containers_ok:
        score += 20
    if existence_ok:
        score += 20
    if size_ok:
        score += 20
    if sha256_ok:
        score += 20

    return score

def _aggregate_stats(meta):
    total_size = 0
    blob_count = 0
    created = None
    modified = None

    for title, note_id in _iter_notes(meta):
        note_info = meta["notes"][title][note_id]
        note_created = note_info.get("created")
        note_modified = note_info.get("modified")

        if note_created and (created is None or note_created < created):
            created = note_created

        if note_modified and (modified is None or note_modified > modified):
            modified = note_modified

        try:
            _, note_meta = _load_note_meta(note_id)
            total_size += note_meta.get("encrypted_size", 0)
            blob_count += note_meta.get("blob_count", 0)

        except Exception:
            pass

    return created, modified, total_size, blob_count

def vault_health():
    with open(META_FILE, "r") as meta_ctn:
        meta = json.load(meta_ctn)

    metadata_ok = verify_metadata()
    containers_ok = verify_containers(meta)
    existence_ok = verify_blob_existence(meta)
    size_ok = verify_blob_size(meta)
    sha256_ok = verify_sha256(meta)

    backup_count = count_backup()
    score = calc_score(metadata_ok, containers_ok, existence_ok, size_ok, sha256_ok)

    created, modified, total_size, blob_count = _aggregate_stats(meta)

    return{
        "score": score,
        "created": created,
        "modified": modified,
        "total_size": total_size,
        "blob_count": blob_count,
        "metadata": metadata_ok,
        "containers": containers_ok,
        "existence": existence_ok,
        "size": size_ok,
        "sha256": sha256_ok,
        "backups": backup_count
    }