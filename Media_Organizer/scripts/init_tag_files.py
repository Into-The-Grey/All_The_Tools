import os
import json

# Set path to config folder
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "config")
os.makedirs(BASE_PATH, exist_ok=True)

SFW_TAG_FILE = os.path.join(BASE_PATH, "tags_sfw.json")
NSFW_TAG_FILE = os.path.join(BASE_PATH, "tags_nsfw.json")

DEFAULT_SFW_TAGS = [
    "dog",
    "cat",
    "person",
    "beach",
    "sunset",
    "car",
    "mountain",
    "flower",
    "food",
    "sky",
]

DEFAULT_NSFW_TAGS = ["nude", "sex", "cleavage", "underwear", "porn", "hentai"]


def init_tag_file(path, default_tags):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_tags = json.load(f)
        except Exception:
            existing_tags = []
    else:
        existing_tags = []

    tag_set = set(existing_tags + default_tags)
    sorted_tags = sorted(tag_set)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted_tags, f, indent=2)

    print(f"[✓] Updated {os.path.basename(path)} with {len(sorted_tags)} tags.")


if __name__ == "__main__":
    init_tag_file(SFW_TAG_FILE, DEFAULT_SFW_TAGS)
    init_tag_file(NSFW_TAG_FILE, DEFAULT_NSFW_TAGS)
    print("\nAll tag files initialized.")
