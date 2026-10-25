import os
import shutil
import sqlite3
import hashlib
from datetime import datetime

backup_dir = "backups/snapshot_phase1_pre_cleanup"
os.makedirs(backup_dir, exist_ok=True)

# 1. Consistent SQLite Online Backup (integrating WAL pages)
backup_db_path = os.path.join(backup_dir, "aicte_consistent_backup.db")
print(f"Executing SQLite online backup from data/aicte.db to {backup_db_path}...")

src_conn = sqlite3.connect("file:data/aicte.db?mode=ro", uri=True)
dst_conn = sqlite3.connect(backup_db_path)
with dst_conn:
    src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()

# 2. Raw copy of data/aicte.db, data/aicte.db-wal, data/aicte.db-shm
for fname in ["aicte.db", "aicte.db-wal", "aicte.db-shm"]:
    src_file = os.path.join("data", fname)
    if os.path.exists(src_file):
        dst_file = os.path.join(backup_dir, f"raw_{fname}")
        with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
            while chunk := sf.read(65536):
                df.write(chunk)
        print(f"Copied raw {src_file} -> {dst_file}")

# 3. Snapshot of storage/documents
backup_docs_dir = os.path.join(backup_dir, "documents")
if os.path.exists("storage/documents"):
    if os.path.exists(backup_docs_dir):
        shutil.rmtree(backup_docs_dir)
    shutil.copytree("storage/documents", backup_docs_dir)
    print(f"Snapshot created for storage/documents -> {backup_docs_dir}")

# 4. Compute file sizes, timestamps, SHA-256 for all snapshot artifacts
def inspect_file(filepath):
    stat = os.stat(filepath)
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return {
        "path": filepath,
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "sha256": h.hexdigest()
    }

print("\n--- Snapshot Integrity Manifest ---")
for f in os.listdir(backup_dir):
    full_path = os.path.join(backup_dir, f)
    if os.path.isfile(full_path):
        info = inspect_file(full_path)
        print(f"{info['path']}: {info['size']} bytes | mtime={info['mtime']} | SHA256={info['sha256']}")

# Verify row counts in consistent backup
chk_conn = sqlite3.connect(f"file:{backup_db_path}?mode=ro", uri=True)
chk_cur = chk_conn.cursor()
chk_cur.execute("SELECT count(*) FROM users;")
users_cnt = chk_cur.fetchone()[0]
chk_cur.execute("SELECT count(*) FROM applications;")
apps_cnt = chk_cur.fetchone()[0]
chk_cur.execute("SELECT count(*) FROM documents;")
docs_cnt = chk_cur.fetchone()[0]
chk_cur.execute("SELECT count(*) FROM audit_events;")
audits_cnt = chk_cur.fetchone()[0]
chk_conn.close()

print(f"\nConsistent Backup Verified: users={users_cnt}, applications={apps_cnt}, documents={docs_cnt}, audit_events={audits_cnt}")
