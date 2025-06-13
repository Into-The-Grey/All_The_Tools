import os
import sys
import json
import argparse
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.LIGHTGREEN_EX}
██ ███    ██ ██ ████████     ████████  █████  ████████  ██████  ██    ██ 
██ ████   ██ ██    ██           ██    ██   ██    ██    ██    ██  ██  ██  
██ ██ ██  ██ ██    ██           ██    ███████    ██    ██    ██   ████   
██ ██  ██ ██ ██    ██           ██    ██   ██    ██    ██    ██    ██    
██ ██   ████ ██    ██           ██    ██   ██    ██     ██████     ██    
{Style.RESET_ALL}
"""

print(BANNER)
print(
    Fore.LIGHTGREEN_EX
    + ">>> Initialize Tag Files (Flagship Mode) <<<"
    + Style.RESET_ALL
)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SFW_TAG_FILE = os.path.join(CONFIG_DIR, "tags_sfw.json")
NSFW_TAG_FILE = os.path.join(CONFIG_DIR, "tags_nsfw.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
ERROR_LOG = os.path.join(
    LOGS_DIR, f"init_tag_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)

# --- ARGS ---
parser = argparse.ArgumentParser(description="Initialize tag vocab files (with gusto).")
parser.add_argument("--dry-run", action="store_true", help="Preview, no changes made")
args = parser.parse_args()

# --- DEFAULT TAGS ---
default_sfw_tags = [
    "person",
    "face",
    "cat",
    "dog",
    "animal",
    "outdoor",
    "nature",
    "city",
    "food",
    "landscape",
    "portrait",
    "vehicle",
    "indoor",
    "text",
    "selfie",
]
default_nsfw_tags = [
    "nudity",
    "suggestive",
    "underwear",
    "explicit",
    "lingerie",
    "bare_skin",
]


def create_tag_file(path, tags, label):
    if os.path.exists(path):
        print(
            Fore.YELLOW + f"⚠️ {label} tag file already exists: {path}" + Style.RESET_ALL
        )
        return False
    if args.dry_run:
        print(
            Fore.CYAN
            + f"[DRY RUN] Would create {label} tag file: {path}"
            + Style.RESET_ALL
        )
        return True
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted(tags), f, indent=2)
        print(Fore.GREEN + f"✅ Created {label} tag file: {path}" + Style.RESET_ALL)
        return True
    except Exception as e:
        print(
            Fore.RED
            + f"❌ Failed to create {label} tag file: {path} ({e})"
            + Style.RESET_ALL
        )
        with open(ERROR_LOG, "a", encoding="utf-8") as errlog:
            errlog.write(f"{label} file error: {path}: {e}\n")
        return False


created = 0
created += create_tag_file(SFW_TAG_FILE, default_sfw_tags, "SFW")
created += create_tag_file(NSFW_TAG_FILE, default_nsfw_tags, "NSFW")

if created == 0:
    print(
        Fore.YELLOW + "No new tag files created (all already exist)." + Style.RESET_ALL
    )
elif not args.dry_run:
    print(
        Fore.GREEN
        + f"\n🎉 Done! {created} tag vocab files initialized."
        + Style.RESET_ALL
    )
if args.dry_run:
    print(Fore.CYAN + "[Dry Run] No files were actually created." + Style.RESET_ALL)
else:
    print(Fore.CYAN + "Tag vocab ready for the pipeline!" + Style.RESET_ALL)
