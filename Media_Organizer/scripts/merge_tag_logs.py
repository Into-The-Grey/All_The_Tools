import os
import sys
import json
import csv
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_PATH, "logs")
MEDIA_TAGS = os.path.join(LOGS_DIR, "media_tags.tsv")
VIDEO_TAGS = os.path.join(LOGS_DIR, "video_tags.tsv")
NSFW_LOG = os.path.join(LOGS_DIR, "nsfw_log.csv")
OUTPUT_JSONL = os.path.join(LOGS_DIR, "media_index.jsonl")


def read_tags_tsv(tsv_path):
    tag_data = {}
    if os.path.exists(tsv_path):
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None)
            for row in reader:
                if row:
                    tag_data[row[0]] = [t for t in row[1:] if t]
    return tag_data


def read_nsfw_log(csv_path):
    nsfw_data = {}
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nsfw_data[row["File"]] = {
                    "classification": row["Classification"].strip().lower(),
                    "unsafe_score": float(row["UnsafeScore"]),
                }
    return nsfw_data


def get_capture_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return None


if __name__ == "__main__":
    img_tag_data = read_tags_tsv(MEDIA_TAGS)
    vid_tag_data = read_tags_tsv(VIDEO_TAGS)
    nsfw_data = read_nsfw_log(NSFW_LOG)

    index = []
    for data in (img_tag_data, vid_tag_data):
        for fpath, tags in data.items():
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

    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for item in index:
            out.write(json.dumps(item) + "\n")

    print(f"[✓] Combined index written to: {OUTPUT_JSONL}")
    print(f"[✓] {len(index)} entries saved.")
