import sys

# --- Allow for extra positional arg (e.g. media directory) and ignore it ---
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    del sys.argv[1]

import os
import json
import argparse
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.RED}
███    ██ ███████ ██████  ████████ ███████ ██████      ████████ ██████  
████   ██ ██      ██   ██    ██    ██      ██   ██        ██    ██   ██ 
██ ██  ██ █████   ██████     ██    █████   ██████         ██    ██████  
██  ██ ██ ██      ██   ██    ██      ██   ██        ██    ██   ██   ██ 
██   ████ ███████ ██   ██    ██    ███████ ██   ██        ██    ██   ██ 
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.RED + ">>> Detect NSFW Images (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")
NSFW_LOG = os.path.join(LOGS_DIR, f"nsfw_log_{datetime.now():%Y%m%d_%H%M%S}.csv")
ERROR_LOG = os.path.join(
    LOGS_DIR, f"detect_nsfw_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "detect_nsfw_checkpoint.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Detect NSFW images (auto-backend, pipeline, with gusto)."
)
parser.add_argument("--dry-run", action="store_true", help="Preview, no changes made")
parser.add_argument(
    "--resume", action="store_true", help="Resume from last checkpoint if available"
)
args = parser.parse_args()

# --- BACKEND AUTO-DETECTION ---
PY_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
NSFW_BACKEND = None

try:
    if sys.version_info < (3, 13):
        from nudenet import NudeClassifier

        NSFW_BACKEND = "nudenet"
except Exception:
    NSFW_BACKEND = None

if NSFW_BACKEND is None:
    try:
        from nsfw_detector import predict  # type: ignore
        import tensorflow as tf  # type: ignore

        NSFW_BACKEND = "nsfw-detector"
    except Exception:
        NSFW_BACKEND = None

if NSFW_BACKEND is None:
    print(
        Fore.YELLOW
        + f"⚠️ No supported NSFW backend found for Python {PY_VERSION}. Skipping NSFW detection."
        + Style.RESET_ALL
    )
    sys.exit(0)
else:
    print(
        Fore.CYAN
        + f"Using NSFW backend: {NSFW_BACKEND} (Python {PY_VERSION})"
        + Style.RESET_ALL
    )

# --- CONFIG LOAD ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    confidence_threshold = config.get("nsfw_confidence", 0.6)
else:
    config = {}
    confidence_threshold = 0.6


def gather_image_files(organized_dir):
    img_files = []
    for root, _, files in os.walk(organized_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                img_files.append(os.path.join(root, file))
    return img_files


already_checked = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_checked = set(checkpoint.get("checked_files", []))

img_files = [f for f in gather_image_files(ORGANIZED_DIR) if f not in already_checked]
print(Fore.CYAN + f"🖼️ Found {len(img_files)} new images to scan." + Style.RESET_ALL)

if not img_files:
    print(
        Fore.GREEN
        + "All images already scanned for NSFW (resume mode). Exiting."
        + Style.RESET_ALL
    )
    sys.exit(0)

if args.dry_run:
    print(Fore.YELLOW + "[DRY RUN] Previewing, not saving logs." + Style.RESET_ALL)

# --- NSFW SCORING FUNCTION ---
if NSFW_BACKEND == "nudenet":
    classifier = NudeClassifier()  # type: ignore

    def nsfw_score_func(filepath):
        result = classifier.classify(filepath)
        unsafe_score = result[filepath]["unsafe"]
        return unsafe_score

elif NSFW_BACKEND == "nsfw-detector":
    model = predict.load_model()

    def nsfw_score_func(filepath):
        preds = predict.classify(model, filepath)
        unsafe_score = preds[filepath].get("porn", 0) + preds[filepath].get("sexy", 0)
        return unsafe_score


# --- MAIN LOOP ---
results = []
errors = []
for f in img_files:
    try:
        if args.dry_run:
            print(Fore.CYAN + f"[DRY RUN] Would scan: {f}" + Style.RESET_ALL)
            continue
        unsafe_score = nsfw_score_func(f)
        classification = "unsafe" if unsafe_score >= confidence_threshold else "safe"
        results.append((f, classification, unsafe_score))
        print(
            Fore.YELLOW
            + f"🟢 {classification.upper()} [{unsafe_score:.2f}]: {f}"
            + Style.RESET_ALL
        )
    except Exception as e:
        print(Fore.RED + f"❌ Error scanning {f}: {e}" + Style.RESET_ALL)
        errors.append((f, str(e)))

# --- LOGGING ---
if not args.dry_run and results:
    import csv

    with open(NSFW_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File", "Classification", "UnsafeScore"])
        for row in results:
            writer.writerow(row)
    print(Fore.GREEN + f"📝 NSFW log: {NSFW_LOG}" + Style.RESET_ALL)

if errors:
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for fpath, msg in errors:
            f.write(f"{fpath}\t{msg}\n")
    print(Fore.YELLOW + f"⚠️ Errors logged to: {ERROR_LOG}" + Style.RESET_ALL)

if not args.dry_run and results:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"checked_files": [r[0] for r in results]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(
    Fore.GREEN + f"\n🎉 Done! Scanned {len(results)} images for NSFW." + Style.RESET_ALL
)
if args.dry_run:
    print(
        Fore.CYAN
        + "[Dry Run] No logs or files were actually written."
        + Style.RESET_ALL
    )
else:
    print(Fore.CYAN + "Ready for next step: merge_tag_logs.py" + Style.RESET_ALL)
