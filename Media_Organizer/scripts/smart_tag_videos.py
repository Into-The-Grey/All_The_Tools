import sys

# --- Allow for extra positional arg (e.g. media directory) and ignore it if not a flag
if len(sys.argv) > 2 and not sys.argv[1].startswith("-"):
    sys.argv[1] = sys.argv[2]
    sys.argv = [sys.argv[0]] + sys.argv[1:]

import os
import json
import torch  # type: ignore
import cv2  # type: ignore
from PIL import Image
from transformers import CLIPProcessor, CLIPModel  # type: ignore
import csv
import argparse
from tqdm import tqdm
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)
BANNER = f"""
{Fore.YELLOW}
███    ██ ██    ██  ██████  ████████  █████  ████████ ██    ██  ██████  
████   ██ ██    ██ ██    ██    ██    ██   ██    ██    ██    ██ ██    ██ 
██ ██  ██ ██    ██ ██    ██    ██    ███████    ██    ██    ██ ██    ██ 
██  ██ ██ ██    ██ ██    ██    ██    ██   ██    ██    ██    ██ ██    ██ 
██   ████  ██████   ██████     ██    ██   ██    ██     ██████   ██████  
{Style.RESET_ALL}
"""

print(BANNER)
print(Fore.YELLOW + ">>> Smart Tag Videos (Flagship Mode) <<<" + Style.RESET_ALL)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")
SFW_TAG_FILE = os.path.join(BASE_DIR, "config", "tags_sfw.json")
LOG_FILE = os.path.join(LOGS_DIR, f"video_tags_{datetime.now():%Y%m%d_%H%M%S}.tsv")
ERROR_LOG = os.path.join(
    LOGS_DIR, f"video_tag_errors_{datetime.now():%Y%m%d_%H%M%S}.log"
)
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "smart_tag_videos_checkpoint.json")

# --- ARGS ---
parser = argparse.ArgumentParser(
    description="Auto-tag videos with CLIP (flagship mode, with attitude)."
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
    batch_size = config.get("video_batch_size", 24 if torch.cuda.is_available() else 4)
    confidence_threshold = config.get("confidence_threshold", 0.3)
    frame_interval = config.get("video_frame_interval", 1)
    min_duration = config.get("video_min_duration", 1)  # in seconds
else:
    config = {}
    batch_size = 24 if torch.cuda.is_available() else 4
    confidence_threshold = 0.3
    frame_interval = 1
    min_duration = 1

device = "cuda" if torch.cuda.is_available() else "cpu"


def load_or_init_tags(path, default=[]):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return sorted(set(json.load(f)))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


sfw_tags = load_or_init_tags(SFW_TAG_FILE)


def gather_video_files(organized_dir, min_duration=1):
    video_exts = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v", ".webm")
    vid_files = []
    for root, _, files in os.walk(organized_dir):
        for file in files:
            if file.lower().endswith(video_exts):
                path = os.path.join(root, file)
                try:
                    cap = cv2.VideoCapture(path)
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps
                    cap.release()
                    if duration >= min_duration:
                        vid_files.append(path)
                except Exception:
                    continue
    return vid_files


already_tagged = set()
if args.resume and os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    already_tagged = set(checkpoint.get("tagged_videos", []))


def sample_frames(video_path, interval_sec=1):
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = int(fps * interval_sec)
        for frame_no in range(0, frame_count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret:
                continue
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(img))
        cap.release()
    except Exception:
        pass
    return frames


def batch_tag_images(images, tag_list, batch_size, device, confidence_threshold):
    tags_per_img = []
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    for i in range(0, len(images), batch_size):
        batch_imgs = images[i : i + batch_size]
        if not batch_imgs:
            continue
        try:
            inputs = processor(
                text=tag_list, images=batch_imgs, return_tensors="pt", padding=True
            )
            inputs = {
                k: v.to(device) if torch.is_tensor(v) else v for k, v in inputs.items()
            }
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()
            for probs_img in probs:
                tags = [
                    tag
                    for tag, prob in zip(tag_list, probs_img)
                    if prob >= confidence_threshold
                ]
                tags_per_img.append(tags)
        except Exception as e:
            for img_idx in range(len(batch_imgs)):
                tags_per_img.append([])
    return tags_per_img


vid_files = [
    f
    for f in gather_video_files(ORGANIZED_DIR, min_duration)
    if f not in already_tagged
]
print(
    Fore.CYAN
    + f"📹 Found {len(vid_files)} new videos to tag. Batch size: {batch_size}, Device: {device}"
    + Style.RESET_ALL
)

if not vid_files:
    print(
        Fore.GREEN
        + "All videos already tagged (resume mode). Exiting."
        + Style.RESET_ALL
    )
    sys.exit(0)

if args.dry_run:
    print(
        Fore.YELLOW + "[DRY RUN] Previewing tags, not saving changes." + Style.RESET_ALL
    )

model = None
processor = None
all_new_tags = set(sfw_tags)
log_rows = []
errors = []

pbar = tqdm(
    total=len(vid_files), desc="🎬 Tagging videos", unit="video", colour="yellow"
)
for vfile in vid_files:
    try:
        frames = sample_frames(vfile, interval_sec=frame_interval)
        if not frames:
            errors.append((vfile, "No frames found"))
            pbar.update(1)
            continue
        if not model or not processor:
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        tags_per_frame = batch_tag_images(
            frames, sfw_tags, batch_size, device, confidence_threshold
        )
        tag_counts = {}
        for taglist in tags_per_frame:
            for tag in taglist:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            min_count = max(1, int(len(frames) * 0.2))
            final_tags = [
                tag for tag, count in tag_counts.items() if count >= min_count
            ]
        else:
            final_tags = []
        all_new_tags.update(final_tags)
        log_rows.append([vfile] + final_tags)
        print(
            Fore.YELLOW
            + f"✅ Tagged {os.path.basename(vfile)}: {', '.join(final_tags) if final_tags else '(none)'}"
            + Style.RESET_ALL
        )
    except Exception as e:
        errors.append((vfile, f"Tagging failed: {e}"))
        print(Fore.RED + f"❌ Error tagging {vfile}: {e}" + Style.RESET_ALL)
    pbar.update(1)
pbar.close()

if not args.dry_run and log_rows:
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["FilePath", "Tags..."])
        writer.writerows(log_rows)
    print(Fore.GREEN + f"📝 Video tag log: {LOG_FILE}" + Style.RESET_ALL)
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
        json.dump({"tagged_videos": [row[0] for row in log_rows]}, f, indent=2)
    print(Fore.CYAN + f"Checkpoint written to {CHECKPOINT_FILE}" + Style.RESET_ALL)

print(Fore.GREEN + f"\n🎉 Done! Tagged {len(log_rows)} videos." + Style.RESET_ALL)
if args.dry_run:
    print(
        Fore.CYAN + "[Dry Run] No tags or logs were actually saved." + Style.RESET_ALL
    )
else:
    print(Fore.CYAN + "Ready for next step: merge_tag_logs.py" + Style.RESET_ALL)
