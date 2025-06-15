import os
import json


def load_url_cache(cache_file):
    if not os.path.exists(cache_file):
        return set()
    with open(cache_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data.get("urls", []))
        except Exception:
            return set()


def save_url_cache(urls, cache_file):
    urls = list(set(urls))
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({"urls": urls}, f, indent=2)
