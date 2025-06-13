import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from PIL import Image, ExifTags
from pymediainfo import MediaInfo
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.BLUE}
 ██████  ██████  ███    ██  ██████  ██████   █████  ███████ ██    ██ 
██      ██    ██ ████   ██ ██    ██ ██   ██ ██   ██ ██      ██    ██ 
██      ██    ██ ██ ██  ██ ██    ██ ██████  ███████ ███████ ██    ██ 
██      ██    ██ ██  ██ ██ ██    ██ ██   ██ ██   ██      ██  ██  ██  
 ██████  ██████  ██   ████  ██████  ██   ██ ██   ██ ███████   ████   
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.MAGENTA + ">>> Organize Media by Date (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")
os.makedirs(ORGANIZED_DIR, exist_ok=True)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "organize_by_date_checkpoint.json")
ERROR_LOG = os.path.join(
    LOGS_DIR, f"organize_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
MOVES_LOG = os.path.join(
    LOGS_DIR, f"organized_moves_{datetime.now():%Y%m%d_%H%M%S}.csv"
)

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Organize media into YYYY/MM/DD folders (with attitude)."
)
parser.add_argument("input_dir", help="Media input directory")
parser.add_argument(
    "--dry-run", action="store_true", help="Preview all moves/copies, make no changes"
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


def get_image_date(path):
    try:
        img = Image.open(path)
        exif = img.getexif()
        if exif:
            date = exif.get(36867)  # 36867 = DateTimeOriginal
            if date:
                return datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


from pymediainfo import MediaInfo


def get_video_date(path):
    try:
        info = MediaInfo.parse(path)
        # Extra strict: bail out if info is a string (Pylance paranoia)
        if isinstance(info, str) or not hasattr(info, "tracks"):
            return None
        for track in info.tracks:
            if getattr(track, "track_type", None) == "General":
                for key in ["recorded_date", "encoded_date", "tagged_date"]:
                    value = getattr(track, key, None)
                    if value:
                        try:
                            # Try parsing ISO date first
                            return datetime.fromisoformat(value.split("T")[0])
                        except Exception:
                            try:
                                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                continue
    except Exception:
        pass
    return None


def get_fallback_date(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except Exception:
        return None


def get_media_date(path):
    ext = os.path.splitext(path)[1].lower()
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".heic"}
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v", ".webm"}
    if ext in image_exts:
        return get_image_date(path) or get_fallback_date(path)
    elif ext in video_exts:
        return get_video_date(path) or get_fallback_date(path)
    else:
        return get_fallback_date(path)


# --- Gather Files ---
media_files = []
for root, _, files in os.walk(args.input_dir):
    for filename in files:
        file_path = os.path.join(root, filename)
        try:
            if os.path.getsize(file_path) >= min_size_kb * 1024:
                media_files.append(file_path)
        except Exception:
            continue

already_moved = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_moved = set(checkpoint.get("organized_files", []))

errors = []
moves = []
progress = tqdm(
    total=len(media_files), desc="📁 Organizing files", unit="file", colour="blue"
)

for file_path in media_files:
    if file_path in already_moved:
        progress.update(1)
        continue
    try:
        date = get_media_date(file_path)
        if date:
            year, month, day = (
                date.strftime("%Y"),
                date.strftime("%m"),
                date.strftime("%d"),
            )
            dest_dir = os.path.join(ORGANIZED_DIR, year, month, day)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(file_path))
            counter = 1
            while os.path.exists(dest_path):
                base, ext = os.path.splitext(os.path.basename(file_path))
                dest_path = os.path.join(dest_dir, f"{base}_dup{counter}{ext}")
                counter += 1
            if args.dry_run:
                print(
                    Fore.CYAN
                    + f"[DRY RUN] Would move: {file_path} → {dest_path}"
                    + Style.RESET_ALL
                )
            else:
                shutil.move(file_path, dest_path)
                print(
                    Fore.YELLOW
                    + f"🟢 Moved: {file_path} → {dest_path}"
                    + Style.RESET_ALL
                )
            moves.append((file_path, dest_path))
        else:
            errors.append((file_path, "No valid date"))
            print(Fore.YELLOW + f"⚠️ No date found: {file_path}" + Style.RESET_ALL)
    except Exception as e:
        errors.append((file_path, str(e)))
        print(Fore.RED + f"❌ Error moving {file_path}: {e}" + Style.RESET_ALL)
    progress.update(1)
progress.close()

if not args.dry_run and moves:
    with open(MOVES_LOG, "w", encoding="utf-8") as f:
        f.write("Source,Destination\n")
        for src, dst in moves:
            f.write(f"{src},{dst}\n")
    print(Fore.GREEN + f"📝 Moves log saved to {MOVES_LOG}" + Style.RESET_ALL)

if errors:
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for fpath, msg in errors:
            f.write(f"{fpath},{msg}\n")
    print(Fore.YELLOW + f"⚠️ Errors logged to: {ERROR_LOG}" + Style.RESET_ALL)

if not args.dry_run:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"organized_files": [m[0] for m in moves]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(Fore.GREEN + f"\n🎉 Done! Organized {len(moves)} files." + Style.RESET_ALL)
if args.dry_run:
    print(Fore.CYAN + "[Dry Run] No files were actually moved." + Style.RESET_ALL)
else:
    print(Fore.CYAN + "Ready for next step: smart_tag_images.py" + Style.RESET_ALL)
