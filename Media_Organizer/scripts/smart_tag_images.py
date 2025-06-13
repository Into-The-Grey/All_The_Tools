import os
import sys
import json
import torch # type: ignore
from PIL import Image
from transformers import CLIPProcessor, CLIPModel # type: ignore
import csv
import argparse
from tqdm import tqdm
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.MAGENTA}
███████╗███╗   ███╗ █████╗ ██████╗ ████████╗     ████████╗ █████╗  ██████╗ 
██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝     ╚══██╔══╝██╔══██╗██╔═══██╗
█████╗  ██╔████╔██║███████║██████╔╝   ██║           ██║   ███████║██║   ██║
██╔══╝  ██║╚██╔╝██║██╔══██║██╔══██╗   ██║           ██║   ██╔══██║██║   ██║
███████╗██║ ╚═╝ ██║██║  ██║██║  ██║   ██║           ██║   ██║  ██║╚██████╔╝
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝           ╚═╝   ╚═╝  ╚═╝ ╚═════╝ 
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.MAGENTA + ">>> Smart Tag Images (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")
SFW_TAG_FILE = os.path.join(BASE_DIR, "config", "tags_sfw.json")
LOG_FILE = os.path.join(LOGS_DIR, f"media_tags_{datetime.now():%Y%m%d_%H%M%S}.tsv")
ERROR_LOG = os.path.join(
    LOGS_DIR, f"image_tag_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "smart_tag_images_checkpoint.json")

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Auto-tag images with CLIP (flagship mode, with attitude)."
)
parser.add_argument(
    "input_dir", help="Media input directory (ignored, tags Organized/ only)"
)
parser.add_argument(
    "--dry-run", action="store_true", help="Preview all tagging, make no changes"
)
parser.add_argument(
    "--resume", action="store_true", help="Resume from last checkpoint if available"
)
args = parser.parse_args()

# --- CONFIG LOAD ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    batch_size = config.get("batch_size", 48 if torch.cuda.is_available() else 6)
    confidence_threshold = config.get("confidence_threshold", 0.3)
else:
    config = {}
    batch_size = 48 if torch.cuda.is_available() else 6
    confidence_threshold = 0.3

device = "cuda" if torch.cuda.is_available() else "cpu"


# --- TAG VOCAB ---
def load_or_init_tags(path, default=[]):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return sorted(set(json.load(f)))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


sfw_tags = load_or_init_tags(SFW_TAG_FILE)


def gather_image_files(organized_dir):
    img_files = []
    for root, _, files in os.walk(organized_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                img_files.append(os.path.join(root, file))
    return img_files


already_tagged = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_tagged = set(checkpoint.get("tagged_files", []))


def batch_tag_images(filepaths, tag_list, batch_size, device, confidence_threshold):
    tags_per_file = []
    all_new_tags = set(tag_list)
    errors = []
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    pbar = tqdm(
        total=len(filepaths), desc="🏷️ Tagging images", unit="img", colour="magenta"
    )
    for i in range(0, len(filepaths), batch_size):
        batch_files = filepaths[i : i + batch_size]
        images = []
        valid_files = []
        for f in batch_files:
            try:
                img = Image.open(f).convert("RGB")
                images.append(img)
                valid_files.append(f)
            except Exception as e:
                print(
                    f"{Fore.YELLOW}⚠️ Skipping unreadable image: {f} ({e}){Style.RESET_ALL}"
                )
                errors.append((f, str(e)))
        if not images:
            pbar.update(len(batch_files))
            continue
        try:
            inputs = processor(
                text=tag_list, images=images, return_tensors="pt", padding=True
            )
            inputs = {
                k: v.to(device) if torch.is_tensor(v) else v for k, v in inputs.items()
            }
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()
            for idx, probs_per_img in enumerate(probs):
                tags = [
                    tag
                    for tag, prob in zip(tag_list, probs_per_img)
                    if prob >= confidence_threshold
                ]
                tags_per_file.append((valid_files[idx], tags))
                all_new_tags.update(tags)
            pbar.update(len(images))
        except Exception as e:
            for f in valid_files:
                print(
                    f"{Fore.RED}❌ Tagging failed for image: {f} ({e}){Style.RESET_ALL}"
                )
                errors.append((f, f"Tagging failed: {e}"))
            pbar.update(len(valid_files))
    pbar.close()
    return tags_per_file, all_new_tags, errors


img_files = [f for f in gather_image_files(ORGANIZED_DIR) if f not in already_tagged]
print(
    Fore.CYAN
    + f"🖼️ Found {len(img_files)} new images to tag. Batch size: {batch_size}, Device: {device}"
    + Style.RESET_ALL
)

if not img_files:
    print(
        Fore.GREEN
        + "All images already tagged (resume mode). Exiting."
        + Style.RESET_ALL
    )
    sys.exit(0)

if args.dry_run:
    print(
        Fore.YELLOW + "[DRY RUN] Previewing tags, not saving changes." + Style.RESET_ALL
    )

tags_per_file, all_new_tags, errors = batch_tag_images(
    img_files, sfw_tags, batch_size, device, confidence_threshold
)

# --- LOGGING ---
if not args.dry_run and tags_per_file:
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["FilePath", "Tags..."])
        for file, tags in tags_per_file:
            writer.writerow([file] + tags)
    print(Fore.GREEN + f"📝 Tag log: {LOG_FILE}" + Style.RESET_ALL)
    os.makedirs(os.path.dirname(SFW_TAG_FILE), exist_ok=True)
    with open(SFW_TAG_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(all_new_tags), f, indent=2)
    print(Fore.CYAN + f"🧠 SFW tag list updated: {SFW_TAG_FILE}" + Style.RESET_ALL)

if errors:
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for fpath, msg in errors:
            f.write(f"{fpath}\t{msg}\n")
    print(Fore.YELLOW + f"⚠️ Errors logged to: {ERROR_LOG}" + Style.RESET_ALL)

if not args.dry_run:
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"tagged_files": [x[0] for x in tags_per_file]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(Fore.GREEN + f"\n🎉 Done! Tagged {len(tags_per_file)} images." + Style.RESET_ALL)
if args.dry_run:
    print(
        Fore.CYAN + "[Dry Run] No tags or logs were actually saved." + Style.RESET_ALL
    )
else:
    print(Fore.CYAN + "Ready for next step: smart_tag_videos.py" + Style.RESET_ALL)
