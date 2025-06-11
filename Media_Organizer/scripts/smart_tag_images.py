import os
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

# === INIT CLIP MODEL ===
print("📦 Loading CLIP model...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# === LOAD/CREATE TAG FILE ===
def load_or_init_tags(path, default=[]):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return sorted(set(json.load(f)))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


sfw_tags = load_or_init_tags(SFW_TAG_FILE)


# === TAGGING FUNCTION ===
def tag_image(img_path, tag_list):
    image = Image.open(img_path).convert("RGB")
    inputs = processor(text=tag_list, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)[0].tolist()
    return [
        (tag, prob)
        for tag, prob in zip(tag_list, probs)
        if prob >= CONFIDENCE_THRESHOLD
    ]


# === WALK FILES AND TAG ===
all_new_tags = set(sfw_tags)
log_rows = []

print("\n🔍 Tagging images...")
for root, _, files in os.walk(ORGANIZED_DIR):
    for file in files:
        if not file.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
            continue
        path = os.path.join(root, file)
        try:
            tags = tag_image(path, sfw_tags)
            tag_names = [t[0] for t in tags]
            new_tags = set(tag_names) - set(sfw_tags)
            if new_tags:
                print(f"➕ New tags from {file}: {new_tags}")
                all_new_tags.update(new_tags)

            log_rows.append([path] + tag_names)
            print(f"✅ Tagged {file} with: {', '.join(tag_names)}")
        except Exception as e:
            print(f"❌ Error tagging {file}: {e}")

# === SAVE UPDATED TAG FILE ===
os.makedirs(os.path.dirname(SFW_TAG_FILE), exist_ok=True)
with open(SFW_TAG_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted(all_new_tags), f, indent=2)

# === SAVE LOG FILE ===
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["FilePath", "Tags..."])
    writer.writerows(log_rows)

print("\n✅ Done tagging.")
print(f"📄 Tag log: {LOG_FILE}")
print(f"🧠 SFW tag list updated: {SFW_TAG_FILE}")
