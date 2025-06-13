import os
import sys
import json
import torch # type: ignore
from PIL import Image
from transformers import CLIPProcessor, CLIPModel # type: ignore
import csv

# === CONFIG ===
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGANIZED_DIR = os.path.join(BASE_PATH, "Organized")
SFW_TAG_FILE = os.path.join(BASE_PATH, "config", "tags_sfw.json")
LOG_FILE = os.path.join(BASE_PATH, "logs", "media_tags.tsv")
CONFIDENCE_THRESHOLD = 0.3


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


def batch_tag_images(filepaths, tag_list, batch_size, device):
    tags_per_file = []
    all_new_tags = set(tag_list)
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
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
                print(f"⚠️ Skipping unreadable image: {f} ({e})")
        if not images:
            continue
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
                if prob >= CONFIDENCE_THRESHOLD
            ]
            tags_per_file.append((valid_files[idx], tags))
            all_new_tags.update(tags)
    return tags_per_file, all_new_tags


if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 48 if device == "cuda" else 6

    print(
        f"🔍 Tagging images in: {ORGANIZED_DIR} (Batch size: {batch_size}, Device: {device})"
    )
    img_files = gather_image_files(ORGANIZED_DIR)
    print(f"🖼️ Found {len(img_files)} images to tag.")

    tags_per_file, all_new_tags = batch_tag_images(
        img_files, sfw_tags, batch_size, device
    )

    os.makedirs(os.path.dirname(SFW_TAG_FILE), exist_ok=True)
    with open(SFW_TAG_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(all_new_tags), f, indent=2)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["FilePath", "Tags..."])
        for file, tags in tags_per_file:
            writer.writerow([file] + tags)

    print(f"\n✅ Done. Tagged {len(tags_per_file)} images.")
    print(f"📄 Tag log: {LOG_FILE}")
    print(f"🧠 SFW tag list updated: {SFW_TAG_FILE}")
