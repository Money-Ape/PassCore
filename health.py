import json, hashlib
from pathlib import Path
from backup import META_FILE, CONTAINER_DIR, BACKUP_ROOT

def sha256_blob(shafile_path):
    hh = hashlib.sha256() # hash helper to cross check modifixation of any blobs

    with open(shafile_path, "rb") as bsha:
        while chunk := bsha.read(8192): # Read 8KB at a time 
            hh.update(chunk)

    return hh.hexdigest() # return hexadecimal hash string.!

def verify_metadata():
    try:
        with open(META_FILE, "r") as vmeta:
            meta = json.load(vmeta)
        
        required = ["created", "modified", "total_size", "blob_count", "blobs"]
        return all(key in meta for key in required)
    
    except Exception:
        return False
    
def verify_containers(meta):
    for info in meta["blobs"].values():
        container_id = info["container"]
        container_path = Path(CONTAINER_DIR / container_id)

        if not container_path.exists():
            return False
    
    return True

def verify_blob_existence(meta):
    for blob_name, info in meta["blobs"].items():
        blob_path = Path(CONTAINER_DIR / info["container"] / blob_name)

        if not blob_path.exists():
            return False
    
    return True

def verify_blob_size(meta):
    for blob_name, info in meta["blobs"].items():
        blob_path = Path(CONTAINER_DIR / info["container"] / blob_name)

        if blob_path.stat().st_size != info["size"]:
            return False
        
    return True

def verify_sha256(meta):
    for blob_name, info in meta["blobs"].items():
        blob_path = Path(CONTAINER_DIR / info["container"] / blob_name)

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

    return{
        "score": score,
        "created": meta["created"],
        "modified": meta["modified"],
        "total_size": meta["total_size"],
        "blob_count": meta["blob_count"],
        "metadata": metadata_ok,
        "containers": containers_ok,
        "existence": existence_ok,
        "size": size_ok,
        "sha256": sha256_ok,
        "backups": backup_count
    }

def generate_report():
    report = vault_health()

    return f"""
        Vault Health Report

        Health Score : {report['score']}/100

        Created      : {report['created']}
        Modified     : {report['modified']}

        Blob Count   : {report['blob_count']}
        Vault Size   : {report['total_size']} bytes

        Integrity Checks

        Metadata     : {"PASS" if report['metadata'] else "FAIL"}
        Containers   : {"PASS" if report['containers'] else "FAIL"}
        Blobs        : {"PASS" if report['existence'] else "FAIL"}
        Blob Size    : {"PASS" if report['size'] else "FAIL"}
        SHA256       : {"PASS" if report['sha256'] else "FAIL"}

        Backups Found: {report['backups']}
    """
