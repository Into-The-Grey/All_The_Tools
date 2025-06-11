import os
import sys
import json
import torch # type: ignore
import cv2 # type: ignore
from PIL import Image
from transformers import CLIPProcessor, CLIPModel # type: ignore
import csv

# === CONFIG ===
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGANIZED_DIR = os.path.join(BASE_PATH, "Organized")
SFW_TAG_FILE = os.path.join(BASE_PATH, "config", "tags_sfw.json")
LOG_FILE = os.path.join(BASE_PATH, "logs", "video_tags.tsv")
CONFIDENCE_THRESHOLD = 0.3
FRAME_INTERVAL = 1  # seconds between sampled frames


def load_or_init_tags(path, default=[]):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return sorted(set(json.load(f)))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


sfw_tags = load_or_init_tags(SFW_TAG_FILE)


def gather_video_files(organized_dir):
    video_exts = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v", ".webm")
    vid_files = []
    for root, _, files in os.walk(organized_dir):
        for file in files:
            if file.lower().endswith(video_exts):
                vid_files.append(os.path.join(root, file))
    return vid_files


def sample_frames(video_path, interval_sec=1):
    """Yield PIL Images sampled every interval_sec seconds from a video."""
    frames = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"⚠️ Could not open {video_path}")
        return frames
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    step = int(fps * interval_sec)
    for frame_no in range(0, frame_count, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            continue
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(img))
    cap.release()
    return frames


def batch_tag_images(images, tag_list, batch_size, device, model, processor):
    tags_per_img = []
    for i in range(0, len(images), batch_size):
        batch_imgs = images[i : i + batch_size]
        inputs = processor(
            text=tag_list, images=batch_imgs, return_tensors="pt", padding=True
        )
        inputs = {
            k: v.to(device) if torch.is_tensor(v) else v for k, v in inputs.items()
        }
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()
        for probs_img in probs:
            tags = [
                tag
                for tag, prob in zip(tag_list, probs_img)
                if prob >= CONFIDENCE_THRESHOLD
            ]
            tags_per_img.append(tags)
    return tags_per_img


if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 24 if device == "cuda" else 4

    print(
        f"🎬 Tagging videos in: {ORGANIZED_DIR} (Batch size: {batch_size}, Device: {device})"
    )
    vid_files = gather_video_files(ORGANIZED_DIR)
    print(f"📹 Found {len(vid_files)} videos to tag.")

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    all_new_tags = set(sfw_tags)
    log_rows = []

    for vfile in vid_files:
        frames = sample_frames(vfile, interval_sec=FRAME_INTERVAL)
        if not frames:
            print(f"⚠️ Skipping (no frames): {vfile}")
            continue
        tags_per_frame = batch_tag_images(
            frames, sfw_tags, batch_size, device, model, processor
        )
        # Aggregate: tag video if tag appears in >1 frame
        tag_counts = {}
        for taglist in tags_per_frame:
            for tag in taglist:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            min_count = max(
                1, int(len(frames) * 0.2)
            )  # At least 20% of frames must have the tag
            final_tags = [
                tag for tag, count in tag_counts.items() if count >= min_count
            ]
        else:
            final_tags = []
        all_new_tags.update(final_tags)
        log_rows.append([vfile] + final_tags)
        print(
            f"✅ Tagged {os.path.basename(vfile)} with: {', '.join(final_tags) if final_tags else '(none)'}"
        )

    # Save expanded tag set
    os.makedirs(os.path.dirname(SFW_TAG_FILE), exist_ok=True)
    with open(SFW_TAG_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(all_new_tags), f, indent=2)

    # Save video tag log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["FilePath", "Tags..."])
        writer.writerows(log_rows)

    print(f"\n✅ Done. Tagged {len(log_rows)} videos.")
    print(f"📄 Video tag log: {LOG_FILE}")
    print(f"🧠 SFW tag list updated: {SFW_TAG_FILE}")
