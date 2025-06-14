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

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Initialize/validate tag vocab files (with gusto)."
)
parser.add_argument("--dry-run", action="store_true", help="Preview, no changes made")
parser.add_argument(
    "--show", action="store_true", help="Print contents of tag files if they exist"
)
parser.add_argument(
    "--reset-sfw", action="store_true", help="Reset SFW tags file to default"
)
parser.add_argument(
    "--reset-nsfw", action="store_true", help="Reset NSFW tags file to default"
)
args = parser.parse_args()


def validate_and_print(path, label, default_tags, show=False):
    try:
        with open(path, "r", encoding="utf-8") as f:
            tags = json.load(f)
        tag_count = len(tags)
        print(
            Fore.GREEN
            + f"✅ {label} tag file valid: {path} ({tag_count} tags)"
            + Style.RESET_ALL
        )
        if show:
            preview = tags[:10] if len(tags) > 10 else tags
            print(Fore.CYAN + f"  First tags: {preview}" + Style.RESET_ALL)
        return tag_count
    except Exception as e:
        print(
            Fore.RED
            + f"❌ {label} tag file corrupted or invalid: {e}"
            + Style.RESET_ALL
        )
        with open(ERROR_LOG, "a", encoding="utf-8") as errlog:
            errlog.write(f"{label} validation error: {path}: {e}\n")
        return None


def create_or_reset_tag_file(path, tags, label, do_reset=False):
    if os.path.exists(path) and not do_reset:
        print(
            Fore.YELLOW + f"⚠️ {label} tag file already exists: {path}" + Style.RESET_ALL
        )
        return False
    if args.dry_run:
        print(
            Fore.CYAN
            + f"[DRY RUN] Would {'reset' if do_reset else 'create'} {label} tag file: {path}"
            + Style.RESET_ALL
        )
        return True
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted(tags), f, indent=2)
        print(
            Fore.GREEN
            + f"✅ {'Reset' if do_reset else 'Created'} {label} tag file: {path}"
            + Style.RESET_ALL
        )
        return True
    except Exception as e:
        print(
            Fore.RED
            + f"❌ Failed to write {label} tag file: {path} ({e})"
            + Style.RESET_ALL
        )
        with open(ERROR_LOG, "a", encoding="utf-8") as errlog:
            errlog.write(f"{label} file error: {path}: {e}\n")
        return False


created = 0
reset = 0

# Reset tags if requested
if args.reset_sfw:
    reset += create_or_reset_tag_file(
        SFW_TAG_FILE, default_sfw_tags, "SFW", do_reset=True
    )
if args.reset_nsfw:
    reset += create_or_reset_tag_file(
        NSFW_TAG_FILE, default_nsfw_tags, "NSFW", do_reset=True
    )

# Create if missing, else validate & print
if not os.path.exists(SFW_TAG_FILE):
    created += create_or_reset_tag_file(SFW_TAG_FILE, default_sfw_tags, "SFW")
else:
    validate_and_print(SFW_TAG_FILE, "SFW", default_sfw_tags, show=args.show)
if not os.path.exists(NSFW_TAG_FILE):
    created += create_or_reset_tag_file(NSFW_TAG_FILE, default_nsfw_tags, "NSFW")
else:
    validate_and_print(NSFW_TAG_FILE, "NSFW", default_nsfw_tags, show=args.show)

if created == 0 and reset == 0:
    print(
        Fore.YELLOW
        + "No new tag files created or reset. (All already exist, validated.)"
        + Style.RESET_ALL
    )
elif not args.dry_run:
    print(
        Fore.GREEN
        + f"\n🎉 Done! {created+reset} tag vocab files created or reset."
        + Style.RESET_ALL
    )
if args.dry_run:
    print(
        Fore.CYAN
        + "[Dry Run] No files were actually created or changed."
        + Style.RESET_ALL
    )
else:
    print(Fore.CYAN + "Tag vocab ready for the pipeline!" + Style.RESET_ALL)
