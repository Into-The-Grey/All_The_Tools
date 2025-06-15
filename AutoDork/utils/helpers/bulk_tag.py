import os
import json


def bulk_tag_urls(base_name, results_dir, tag_urls_func, console):
    json_path = os.path.join(results_dir, f"{base_name}.json")
    if not os.path.exists(json_path):
        console.print(f"[red]Results file {json_path} not found![/red]")
        return
    with open(json_path, "r", encoding="utf-8") as jf:
        url_map = json.load(jf)
    urls = list(url_map.keys())
    tags = tag_urls_func(urls)
    tag_path = os.path.join(results_dir, "followup_tags.json")
    with open(tag_path, "w", encoding="utf-8") as tf:
        json.dump(tags, tf, indent=2)
    console.print(f"[bold cyan]Bulk-tagged all URLs in {json_path}[/bold cyan]")
