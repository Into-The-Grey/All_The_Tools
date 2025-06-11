import os
import json
import csv
from datetime import datetime

# === CONFIG ===
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_PATH, "Organized")
TAGS_TSV = os.path.join(BASE_PATH, "logs", "media_tags.tsv")
NSFW_CSV = os.path.join(BASE_PATH, "logs", "nsfw_log.csv")
OUTPUT_JSONL = os.path.join(BASE_PATH, "logs", "media_index.jsonl")

# === Load SFW Tags
tag_data = {}
if os.path.exists(TAGS_TSV):
    with open(TAGS_TSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # skip header
        for row in reader:
            if row:
                path = row[0]
                tags = [t for t in row[1:] if t]
                tag_data[path] = tags

# === Load NSFW Scores
nsfw_data = {}
if os.path.exists(NSFW_CSV):
    with open(NSFW_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nsfw_data[row["File"]] = {
                "classification": row["Classification"].strip().lower(),
                "unsafe_score": float(row["UnsafeScore"]),
            }


# === Build Index
def get_capture_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return None


index = []
for root, _, files in os.walk(MEDIA_DIR):
    for file in files:
        fpath = os.path.join(root, file)
        tags = tag_data.get(fpath, [])
        nsfw_info = nsfw_data.get(
            fpath, {"classification": "unknown", "unsafe_score": 0.0}
        )
        entry = {
            "file": fpath,
            "tags": tags,
            "nsfw": nsfw_info["classification"] == "unsafe",
            "unsafe_score": nsfw_info["unsafe_score"],
            "capture_date": get_capture_date(fpath),
        }
        index.append(entry)

# === Save to JSONL
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
    for item in index:
        out.write(json.dumps(item) + "\n")

print(f"[✓] Combined index written to: {OUTPUT_JSONL}")
print(f"[✓] {len(index)} entries saved.")
