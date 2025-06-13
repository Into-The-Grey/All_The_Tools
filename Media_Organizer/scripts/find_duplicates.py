import os
import sys
import json
import hashlib
import argparse
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "find_duplicates_checkpoint.json")
DUPLICATES_LOG = os.path.join(
    LOGS_DIR, f"duplicate_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
)

# --- ARGS ---
parser = argparse.ArgumentParser(description="Find and log duplicate files by hash.")
parser.add_argument("input_dir", help="Media directory to scan")
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not write/move anything, just print what would happen",
)
parser.add_argument(
    "--resume", action="store_true", help="Resume from last checkpoint if available"
)
args = parser.parse_args()

# --- CONFIG LOAD ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    min_size_kb = config.get("min_file_size_kb", 1)
else:
    config = {}
    min_size_kb = 1  # default: skip files smaller than 1KB

# --- CHECKPOINT RESUME (Not usually needed for this script, but structure provided) ---
start_dir = args.input_dir
resume_hashes = {}
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        resume_data = json.load(f)
    resume_hashes = resume_data.get("hashes", {})


def compute_md5(file_path, chunk_size=8192):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
    except Exception as e:
        print(f"[ERROR] Can't read file: {file_path} — {e}")
        return None
    return hash_md5.hexdigest()


def find_duplicate_files(base_dir, min_kb):
    hash_map = defaultdict(list)
    # Count files for progress bar
    files_to_scan = []
    for root, _, files in os.walk(base_dir):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                if os.path.getsize(file_path) >= min_kb * 1024:
                    files_to_scan.append(file_path)
            except Exception:
                continue
    for file_path in tqdm(
        files_to_scan, desc="Hashing files for duplicates", unit="file"
    ):
        file_hash = compute_md5(file_path)
        if file_hash:
            hash_map[file_hash].append(file_path)
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


if __name__ == "__main__":
    print("🔍 Media Duplicate Finder (Production Mode)")
    print(f"Scanning: {args.input_dir} | Min file size: {min_size_kb} KB")
    print(
        f"Config loaded: {CONFIG_FILE if os.path.exists(CONFIG_FILE) else '[default]'}"
    )
    print(f"Dry run: {args.dry_run}")

    dupes = find_duplicate_files(args.input_dir, min_size_kb)
    print(f"\n✅ Found {len(dupes)} sets of exact duplicates.\n")

    # Log to timestamped CSV
    if not args.dry_run:
        with open(DUPLICATES_LOG, "w", encoding="utf-8") as out:
            out.write("GroupID,Hash,FilePath\n")
            for idx, (file_hash, files) in enumerate(dupes.items(), 1):
                for f in files:
                    out.write(f"{idx},{file_hash},{f}\n")
        print(f"📝 Log saved to {DUPLICATES_LOG}")
        # Write checkpoint for next tool in pipeline
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as cpt:
            json.dump({"completed": True, "hashes": list(dupes.keys())}, cpt, indent=2)
    else:
        print("[Dry Run] No logs written.")

    # Optional: Print summary
    for idx, (file_hash, files) in enumerate(dupes.items(), 1):
        print(f"[Group {idx}] Hash: {file_hash}")
        for f in files:
            print(f"  - {f}")
        print()
