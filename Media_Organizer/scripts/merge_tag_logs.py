import os
import json
import csv
from datetime import datetime

# === CONFIG ===
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_PATH, "Organized")
IMAGE_TAGS_FILE = os.path.join(BASE_PATH, "logs", "media_tags.tsv")
VIDEO_TAGS_FILE = os.path.join(BASE_PATH, "logs", "video_tags.tsv")
NSFW_LOG_FILE = os.path.join(BASE_PATH, "logs", "nsfw_log.csv")
OUTPUT_JSONL = os.path.join(BASE_PATH, "logs", "media_index.jsonl")


# === LOAD TAG LOGS ===
def load_tsv(file_path):
    data = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None)
            for row in reader:
                if row:
                    path = row[0]
                    tags = [t for t in row[1:] if t]
                    data[path] = tags
    return data


# === LOAD NSFW DATA ===
def load_nsfw_log(file_path):
    data = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data[row["File"]] = {
                    "classification": row["Classification"].strip().lower(),
                    "unsafe_score": float(row["UnsafeScore"]),
                }
    return data


# === GET TIMESTAMP ===
def get_capture_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return None


# === MAIN MERGE ===
print("📦 Merging image/video tag logs into unified media index...")
image_tags = load_tsv(IMAGE_TAGS_FILE)
video_tags = load_tsv(VIDEO_TAGS_FILE)
nsfw_data = load_nsfw_log(NSFW_LOG_FILE)

all_paths = set(image_tags.keys()) | set(video_tags.keys())
index = []

for path in sorted(all_paths):
    tags = image_tags.get(path, []) + video_tags.get(path, [])
    nsfw_info = nsfw_data.get(path, {"classification": "unknown", "unsafe_score": 0.0})
    index.append(
        {
            "file": path,
            "tags": sorted(set(tags)),
            "nsfw": nsfw_info["classification"] == "unsafe",
            "unsafe_score": nsfw_info["unsafe_score"],
            "capture_date": get_capture_date(path),
        }
    )

os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for entry in index:
        f.write(json.dumps(entry) + "\n")

print(f"\n✅ Merged index saved to: {OUTPUT_JSONL}")
print(f"🧮 Total entries: {len(index)}")
