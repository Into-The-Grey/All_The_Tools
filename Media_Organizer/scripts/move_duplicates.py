import os
import sys
import json
import shutil
import argparse
from tqdm import tqdm
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.GREEN}
███    ███  ██████  ██    ██ ███████     ██████  ██    ██ ██████  ██    ██ 
████  ████ ██    ██ ██    ██ ██          ██   ██ ██    ██ ██   ██  ██  ██  
██ ████ ██ ██    ██ ██    ██ █████       ██████  ██    ██ ██   ██   ████   
██  ██  ██ ██    ██ ██    ██ ██          ██   ██ ██    ██ ██   ██    ██    
██      ██  ██████   ██████  ███████     ██   ██  ██████  ██████     ██    
{Style.RESET_ALL}
"""

print(BANNER)
print(
    Fore.MAGENTA
    + ">>> Move Duplicates & Log Everything (Flagship Mode) <<<"
    + Style.RESET_ALL
)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DUPLICATES_DIR = os.path.join(BASE_DIR, "Duplicates")
os.makedirs(DUPLICATES_DIR, exist_ok=True)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "move_duplicates_checkpoint.json")


def find_latest_duplicate_log():
    logs = [
        f
        for f in os.listdir(LOGS_DIR)
        if f.startswith("duplicate_log_") and f.endswith(".csv")
    ]
    if not logs:
        print(
            Fore.RED
            + "❌ No duplicate_log_*.csv found! Please run find_duplicates.py first."
            + Style.RESET_ALL
        )
        sys.exit(1)
    logs.sort(reverse=True)
    return os.path.join(LOGS_DIR, logs[0])


# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Move duplicates (production mode, with attitude)."
)
parser.add_argument("input_dir", help="Original media input directory")
parser.add_argument(
    "--dry-run", action="store_true", help="Preview all moves, make no changes"
)
parser.add_argument(
    "--resume", action="store_true", help="Resume from last checkpoint if available"
)
args = parser.parse_args()

DUPLICATE_LOG = find_latest_duplicate_log()
ERROR_LOG = os.path.join(
    LOGS_DIR, f"move_duplicates_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
MOVES_LOG = os.path.join(
    LOGS_DIR, f"moved_duplicates_{datetime.now():%Y%m%d_%H%M%S}.csv"
)

# --- LOAD DUPLICATE GROUPS ---
duplicate_groups = {}
with open(DUPLICATE_LOG, "r", encoding="utf-8") as f:
    next(f)  # Skip header
    for line in f:
        group_id, hashval, fpath = line.strip().split(",", 2)
        duplicate_groups.setdefault(group_id, []).append(fpath)

# --- CHECKPOINT RESUME (structure for future) ---
already_moved = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_moved = set(checkpoint.get("moved_files", []))

errors = []
moves = []
total_files = sum(
    len(paths) - 1 for paths in duplicate_groups.values() if len(paths) > 1
)
progress = tqdm(
    total=total_files, desc="🚚 Moving duplicates", unit="file", colour="green"
)

for group_id, files in duplicate_groups.items():
    if len(files) < 2:
        continue  # Only 1 file: skip
    original = files[0]
    for dup in files[1:]:
        if dup in already_moved:
            progress.update(1)
            continue  # Already handled in resume mode
        try:
            if not os.path.exists(dup):
                msg = f"{Fore.YELLOW}⚠️ Not found: {dup}{Style.RESET_ALL}"
                print(msg)
                errors.append((dup, "Not found"))
                progress.update(1)
                continue
            dest = os.path.join(DUPLICATES_DIR, os.path.basename(dup))
            dest_base, dest_ext = os.path.splitext(dest)
            counter = 1
            while os.path.exists(dest):
                dest = f"{dest_base}_dup{counter}{dest_ext}"
                counter += 1
            if args.dry_run:
                print(
                    Fore.CYAN
                    + f"[DRY RUN] Would move: {dup} → {dest}"
                    + Style.RESET_ALL
                )
            else:
                shutil.move(dup, dest)
                print(
                    Fore.YELLOW
                    + f"🟢 Moved duplicate: {dup} → {dest}"
                    + Style.RESET_ALL
                )
            moves.append((group_id, original, dup, dest))
        except Exception as e:
            print(Fore.RED + f"❌ Failed to move {dup}: {e}" + Style.RESET_ALL)
            errors.append((dup, str(e)))
        progress.update(1)
progress.close()

# --- LOG MOVES & ERRORS ---
if not args.dry_run and moves:
    with open(MOVES_LOG, "w", encoding="utf-8") as f:
        f.write("GroupID,Original,Duplicate,NewLocation\n")
        for group_id, original, dup, dest in moves:
            f.write(f"{group_id},{original},{dup},{dest}\n")
    print(Fore.GREEN + f"📝 Moves log saved to {MOVES_LOG}" + Style.RESET_ALL)

if errors:
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for fpath, msg in errors:
            f.write(f"{fpath},{msg}\n")
    print(Fore.YELLOW + f"⚠️ Errors logged to: {ERROR_LOG}" + Style.RESET_ALL)

# --- WRITE CHECKPOINT ---
if not args.dry_run:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"moved_files": [m[2] for m in moves]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(Fore.GREEN + f"\n🎉 Done! Moved {len(moves)} duplicate files." + Style.RESET_ALL)
if args.dry_run:
    print(Fore.CYAN + "[Dry Run] No files were actually moved." + Style.RESET_ALL)
else:
    print(Fore.CYAN + "Ready for next step: organize_by_date.py" + Style.RESET_ALL)
