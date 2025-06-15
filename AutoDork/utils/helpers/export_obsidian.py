import os
from datetime import datetime


def export_to_obsidian(base_name, url_map, tags_map, base, console):
    obsidian_dir = os.path.join(base, "exports", "obsidian")
    os.makedirs(obsidian_dir, exist_ok=True)
    md_path = os.path.join(obsidian_dir, f"{base_name}.md")
    lines = [
        f"# AutoDork Export — {base_name}",
        "",
        f"Exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Dork Results",
        "",
    ]
    for url, dorks in url_map.items():
        lines.append(f"- [{url}]({url})")
        lines.append(f"  - _Dorks:_ {', '.join(dorks)}")
        if tags_map and url in tags_map and tags_map[url]:
            lines.append(f"  - _Tags:_ {', '.join(tags_map[url])}")
        lines.append("")
    lines.append(f"---\n**Total URLs:** {len(url_map)}")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    console.print(f"[bold green]Exported Obsidian Markdown:[/bold green] {md_path}")
