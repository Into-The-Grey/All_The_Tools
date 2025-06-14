import sys

# --- Allow for extra positional arg (e.g. media directory) and ignore it ---
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    del sys.argv[1]

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.CYAN}
███    ███ ███████ ██████  ███████  ██████      ██    ██  ██████  ███████ 
████  ████ ██      ██   ██ ██      ██    ██     ██    ██ ██    ██ ██      
██ ████ ██ █████   ██████  █████   ██    ██     ██    ██ ██    ██ █████   
██  ██  ██ ██      ██   ██ ██      ██    ██     ██    ██ ██    ██ ██      
██      ██ ███████ ██   ██ ███████  ██████       ██████   ██████  ███████ 
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.MAGENTA + ">>> Merge Tag Logs (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
MEDIA_TAGS = sorted(
    [
        f
        for f in os.listdir(LOGS_DIR)
        if f.startswith("media_tags_") and f.endswith(".tsv")
    ]
)
VIDEO_TAGS = sorted(
    [
        f
        for f in os.listdir(LOGS_DIR)
        if f.startswith("video_tags_") and f.endswith(".tsv")
    ]
)
NSFW_LOG = os.path.join(LOGS_DIR, "nsfw_log.csv")  # May not exist!
OUTPUT_JSONL = os.path.join(
    LOGS_DIR, f"media_index_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
)
ERROR_LOG = os.path.join(
    LOGS_DIR, f"merge_tag_logs_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "merge_tag_logs_checkpoint.json")

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Merge image/video tag logs into a unified index (with gusto)."
)
parser.add_argument(
    "--dry-run", action="store_true", help="Preview merge, no index/logs written"
)
parser.add_argument(
    "--resume", action="store_true", help="Resume from last checkpoint if available"
)
args = parser.parse_args()


def read_tags_tsv(tsv_path):
    tag_data = {}
    try:
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None)
            for row in reader:
                if row:
                    tag_data[row[0]] = [t for t in row[1:] if t]
    except Exception as e:
        print(Fore.RED + f"❌ Failed to read {tsv_path}: {e}" + Style.RESET_ALL)
    return tag_data


def read_nsfw_log(csv_path):
    nsfw_data = {}
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nsfw_data[row["File"]] = {
                        "classification": row["Classification"].strip().lower(),
                        "unsafe_score": float(row["UnsafeScore"]),
                    }
        except Exception as e:
            print(Fore.RED + f"❌ Failed to read NSFW log: {e}" + Style.RESET_ALL)
    return nsfw_data


def get_capture_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return None


# --- CHECKPOINT RESUME ---
already_merged = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_merged = set(checkpoint.get("merged_files", []))

errors = []
index = []


# --- Merge logs ---
def process_log_files(tag_files, nsfw_data, already_merged, errors):
    merged_count = 0
    for file in tag_files:
        tag_data = read_tags_tsv(os.path.join(LOGS_DIR, file))
        for fpath, tags in tag_data.items():
            if fpath in already_merged:
                continue
            nsfw_info = nsfw_data.get(
                fpath, {"classification": "unknown", "unsafe_score": 0.0}
            )
            entry = {
                "file": fpath,
                "tags": tags,
                "nsfw": nsfw_info["classification"] == "unsafe",
                "unsafe_score": nsfw_info["unsafe_score"],
                "capture_date": get_capture_date(fpath),
            }
            index.append(entry)
            merged_count += 1
    return merged_count


# --- Process logs (images/videos) ---
print(Fore.CYAN + "Reading and merging tag logs..." + Style.RESET_ALL)
nsfw_data = read_nsfw_log(NSFW_LOG)
img_count = process_log_files(MEDIA_TAGS, nsfw_data, already_merged, errors)
vid_count = process_log_files(VIDEO_TAGS, nsfw_data, already_merged, errors)

if not args.dry_run:
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for item in index:
            out.write(json.dumps(item) + "\n")
    print(
        Fore.GREEN + f"📝 Combined index written to: {OUTPUT_JSONL}" + Style.RESET_ALL
    )

if errors:
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for msg in errors:
            f.write(msg + "\n")
    print(Fore.YELLOW + f"⚠️ Errors logged to: {ERROR_LOG}" + Style.RESET_ALL)

if not args.dry_run:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"merged_files": [item["file"] for item in index]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(
    Fore.GREEN + f"\n🎉 Done! Merged {img_count+vid_count} entries." + Style.RESET_ALL
)
if args.dry_run:
    print(Fore.CYAN + "[Dry Run] No logs/index actually written." + Style.RESET_ALL)
else:
    print(Fore.CYAN + "Media archive is now fully indexed!" + Style.RESET_ALL)
