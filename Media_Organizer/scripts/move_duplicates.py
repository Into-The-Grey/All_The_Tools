import os
import sys
import hashlib
import shutil
import csv
from collections import defaultdict


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


def find_duplicate_files(base_dir):
    hash_map = defaultdict(list)
    for root, _, files in os.walk(base_dir):
        for name in files:
            file_path = os.path.join(root, name)
            file_hash = compute_md5(file_path)
            if file_hash:
                hash_map[file_hash].append(file_path)
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


def safe_move(src_path, dest_dir, group_id):
    filename = os.path.basename(src_path)
    base, ext = os.path.splitext(filename)
    dest_path = os.path.join(dest_dir, filename)

    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{base}_dup{group_id}_{counter}{ext}")
        counter += 1

    shutil.move(src_path, dest_path)
    return dest_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python move_duplicates.py <input_media_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    duplicates_folder = os.path.join(base_path, "Duplicates")
    logs_folder = os.path.join(base_path, "logs")
    os.makedirs(duplicates_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)

    print("\n⏳ Scanning for duplicates...")
    dupes = find_duplicate_files(input_path)

    log_path = os.path.join(logs_folder, "duplicate_log.csv")
    with open(log_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["GroupID", "Original", "Duplicate"])

        for group_id, (hash_val, paths) in enumerate(dupes.items(), 1):
            original = paths[0]
            print(f"\n[Group {group_id}] Keeping original:\n  {original}")
            for dup in paths[1:]:
                try:
                    moved_path = safe_move(dup, duplicates_folder, group_id)
                    print(f"  Moved duplicate -> {moved_path}")
                    writer.writerow([group_id, original, dup])
                except Exception as e:
                    print(f"  [ERROR] Failed to move {dup}: {e}")

    print(f"\n✅ Done! Moved duplicates to: {duplicates_folder}")
    print(f"📝 Log written to: {log_path}")
