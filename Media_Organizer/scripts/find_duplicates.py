import os
import sys
import json
import hashlib
import argparse
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime
from colorama import Fore, Style, init

# --- SETUP ---
init(autoreset=True)
BANNER = f"""
{Fore.CYAN}
 ██████╗ ██╗███╗   ██╗██████╗     ██████╗ ██╗   ██╗██████╗ ██╗   ██╗
██╔═══██╗██║████╗  ██║██╔══██╗   ██╔═══██╗██║   ██║██╔══██╗╚██╗ ██╔╝
██║   ██║██║██╔██╗ ██║██║  ██║   ██║   ██║██║   ██║██████╔╝ ╚████╔╝ 
██║   ██║██║██║╚██╗██║██║  ██║   ██║   ██║██║   ██║██╔══██╗  ╚██╔╝  
╚██████╔╝██║██║ ╚████║██████╔╝██╗╚██████╔╝╚██████╔╝██║  ██║   ██║   
 ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.MAGENTA + ">>> Media Duplicate Finder (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "find_duplicates_checkpoint.json")
DUPLICATES_LOG = os.path.join(
    LOGS_DIR, f"duplicate_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
)
ERROR_LOG = os.path.join(
    LOGS_DIR, f"duplicate_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Find and log duplicate files by hash (with style)."
)
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
    min_size_kb = 1

# --- CHECKPOINT (structure for future use) ---
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
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Can't read file: {file_path} — {e}")
    return hash_md5.hexdigest()


def find_duplicate_files(base_dir, min_kb, error_log_path):
    hash_map = defaultdict(list)
    files_to_scan = []
    errors = []
    for root, _, files in os.walk(base_dir):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                # Skip symlinks and tiny files
                if os.path.islink(file_path):
                    errors.append((file_path, "Symlink skipped"))
                    continue
                size_kb = os.path.getsize(file_path) / 1024
                if size_kb < min_kb:
                    errors.append((file_path, f"File too small ({size_kb:.1f} KB)"))
                    continue
                files_to_scan.append(file_path)
            except Exception as e:
                errors.append((file_path, f"Stat failed: {e}"))

    pbar = tqdm(files_to_scan, desc="🔍 Hashing files", unit="file", colour="cyan")
    for file_path in pbar:
        try:
            file_hash = compute_md5(file_path)
            if file_hash:
                hash_map[file_hash].append(file_path)
            else:
                errors.append((file_path, "Hash failed"))
        except PermissionError as e:
            errors.append((file_path, str(e)))
            pbar.write(
                Fore.YELLOW + f"⚠️ Permission denied: {file_path}" + Style.RESET_ALL
            )
        except Exception as e:
            errors.append((file_path, str(e)))
            pbar.write(Fore.RED + f"❌ Error: {file_path} — {e}" + Style.RESET_ALL)
    # Log errors
    if errors:
        with open(error_log_path, "w", encoding="utf-8") as elog:
            for path, err in errors:
                elog.write(f"{path},{err}\n")
        print(
            Fore.YELLOW
            + f"\n⚠️ Warnings/Errors logged to: {error_log_path}"
            + Style.RESET_ALL
        )
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}, errors


if __name__ == "__main__":
    print(
        Fore.CYAN
        + f"Scanning: {args.input_dir} | Min file size: {min_size_kb} KB"
        + Style.RESET_ALL
    )
    print(
        Fore.CYAN
        + f"Config loaded: {CONFIG_FILE if os.path.exists(CONFIG_FILE) else '[default]'}"
        + Style.RESET_ALL
    )
    print(Fore.CYAN + f"Dry run: {args.dry_run}\n" + Style.RESET_ALL)

    try:
        dupes, errors = find_duplicate_files(args.input_dir, min_size_kb, ERROR_LOG)
    except Exception as e:
        print(Fore.RED + f"\n❌ FATAL ERROR: {e}" + Style.RESET_ALL)
        sys.exit(1)

    print(
        Fore.GREEN
        + f"\n✅ Found {len(dupes)} sets of exact duplicates.\n"
        + Style.RESET_ALL
    )

    if not args.dry_run and dupes:
        with open(DUPLICATES_LOG, "w", encoding="utf-8") as out:
            out.write("GroupID,Hash,FilePath\n")
            for idx, (file_hash, files) in enumerate(dupes.items(), 1):
                for f in files:
                    out.write(f"{idx},{file_hash},{f}\n")
        print(
            Fore.GREEN + f"📝 Duplicate log saved to {DUPLICATES_LOG}" + Style.RESET_ALL
        )
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as cpt:
            json.dump({"completed": True, "hashes": list(dupes.keys())}, cpt, indent=2)
        print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)
    elif not dupes:
        print(Fore.YELLOW + "No duplicates found. No log written." + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "[Dry Run] No logs written." + Style.RESET_ALL)

    # Optional: Print summary
    for idx, (file_hash, files) in enumerate(dupes.items(), 1):
        print(Fore.MAGENTA + f"[Group {idx}] Hash: {file_hash}" + Style.RESET_ALL)
        for f in files:
            print("  " + Fore.YELLOW + "- " + f + Style.RESET_ALL)
        print()

    print(Fore.GREEN + "🎉 Duplicate scanning complete!" + Style.RESET_ALL)
    print(
        Fore.BLUE
        + "--------------------------------------------------------"
        + Style.RESET_ALL
    )
    print(
        Fore.CYAN + "Ready for next pipeline step: move_duplicates.py" + Style.RESET_ALL
    )
