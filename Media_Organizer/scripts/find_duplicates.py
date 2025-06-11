import os
import sys
import hashlib
from collections import defaultdict


def compute_md5(file_path, chunk_size=8192):
    """Compute MD5 hash for a file (read in binary mode, in chunks)."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
    except Exception as e:
        print(f"[ERROR] Can't read file: {file_path} — {e}")
        return None
    return hash_md5.hexdigest()


def find_duplicate_files(base_dir):
    """Recursively find files with identical MD5 hashes."""
    hash_map = defaultdict(list)
    for root, _, files in os.walk(base_dir):
        for name in files:
            file_path = os.path.join(root, name)
            file_hash = compute_md5(file_path)
            if file_hash:
                hash_map[file_hash].append(file_path)
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    return duplicates


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_duplicates.py <input_media_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    print("🔍 Media Duplicate Finder")

    print("\n⏳ Scanning for duplicates... Please wait.\n")
    dupes = find_duplicate_files(input_path)

    print(f"\n✅ Found {len(dupes)} sets of exact duplicates.\n")
    for idx, (file_hash, files) in enumerate(dupes.items(), 1):
        print(f"[Group {idx}] Hash: {file_hash}")
        for f in files:
            print(f"  - {f}")
        print()
