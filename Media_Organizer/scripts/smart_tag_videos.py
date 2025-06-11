import os
import json
import cv2 # type: ignore
import torch # type: ignore
import csv
from PIL import Image
from transformers import CLIPProcessor, CLIPModel # type: ignore
from tqdm import tqdm

# === CONFIG ===
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(BASE_PATH, "Organized")
SFW_TAG_FILE = os.path.join(BASE_PATH, "config", "tags_sfw.json")
LOG_FILE = os.path.join(BASE_PATH, "logs", "video_tags.tsv")

CONFIDENCE_THRESHOLD = 0.3
FRAME_INTERVAL = 1  # seconds
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 16 if DEVICE == "cuda" else 2

print(f"🔧 Using device: {DEVICE.upper()} | Batch size: {BATCH_SIZE}")

# === INIT CLIP MODEL ===
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(DEVICE)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# === LOAD TAG FILE ===
def load_or_init_tags(path, default=[]):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return sorted(set(json.load(f)))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


sfw_tags = load_or_init_tags(SFW_TAG_FILE)


# === FIND VIDEO FILES ===
def get_video_paths(base_dir):
    valid_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".m4v")
    video_paths = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(valid_exts):
                video_paths.append(os.path.join(root, file))
    return video_paths


# === SAMPLE FRAMES ===
def sample_frames(video_path, interval_sec):
    frames = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval_sec)
    count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            frames.append(img)
        count += 1
    cap.release()
    return frames


# === TAG BATCH OF IMAGES ===
def tag_images(images, tag_list):
    inputs = processor(text=tag_list, images=images, return_tensors="pt", padding=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1).cpu().tolist()

    batch_tags = []
    for prob_row in probs:
        tags = [
            tag for tag, prob in zip(tag_list, prob_row) if prob >= CONFIDENCE_THRESHOLD
        ]
        batch_tags.append(tags)
    return batch_tags


# === MAIN TAGGING LOOP ===
print("\n🎞️ Tagging videos...")
video_paths = get_video_paths(VIDEO_DIR)
log_rows = []
all_new_tags = set(sfw_tags)

for vid_path in tqdm(video_paths, desc="Videos"):
    try:
        frames = sample_frames(vid_path, FRAME_INTERVAL)
        frame_tags = []
        for i in range(0, len(frames), BATCH_SIZE):
            batch = frames[i : i + BATCH_SIZE]
            batch_tags = tag_images(batch, sfw_tags)
            frame_tags.extend(batch_tags)

        # Flatten and deduplicate all tags from all frames
        flat_tags = sorted(set(tag for tags in frame_tags for tag in tags))
        new_tags = set(flat_tags) - set(sfw_tags)
        if new_tags:
            print(f"➕ New tags from {os.path.basename(vid_path)}: {new_tags}")
            all_new_tags.update(new_tags)
        log_rows.append([vid_path] + flat_tags)

    except Exception as e:
        print(f"❌ Error processing {os.path.basename(vid_path)}: {e}")

# === SAVE UPDATED TAG LIST ===
os.makedirs(os.path.dirname(SFW_TAG_FILE), exist_ok=True)
with open(SFW_TAG_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted(all_new_tags), f, indent=2)

# === SAVE LOG FILE ===
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["FilePath", "Tags..."])
    writer.writerows(log_rows)

print("\n✅ Done tagging all videos.")
print(f"📄 Tag log: {LOG_FILE}")
print(f"🧠 SFW tag list updated: {SFW_TAG_FILE}")
