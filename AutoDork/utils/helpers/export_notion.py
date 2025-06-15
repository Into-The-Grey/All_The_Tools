import os
from datetime import datetime


def export_to_notion(base_name, url_map, tags_map, base, console):
    notion_dir = os.path.join(base, "exports", "notion")
    os.makedirs(notion_dir, exist_ok=True)
    md_path = os.path.join(notion_dir, f"{base_name}.md")
    lines = [
        f"# AutoDork Export — {base_name}",
        "",
        f"Exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| URL | Dorks | Tags |",
        "|-----|-------|------|",
    ]
    for url, dorks in url_map.items():
        tags = (
            ", ".join(tags_map[url])
            if tags_map and url in tags_map and tags_map[url]
            else ""
        )
        url_md = f"[{url}]({url})"
        dorks_md = ", ".join(dorks)
        lines.append(f"| {url_md} | {dorks_md} | {tags} |")
    lines.append(f"\n**Total URLs:** {len(url_map)}")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    console.print(f"[bold green]Exported Notion Markdown:[/bold green] {md_path}")
