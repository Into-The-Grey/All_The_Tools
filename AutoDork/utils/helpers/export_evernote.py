import os
from datetime import datetime


def export_to_evernote(base_name, url_map, tags_map, base, console):
    en_dir = os.path.join(base, "exports", "evernote")
    os.makedirs(en_dir, exist_ok=True)
    enex_path = os.path.join(en_dir, f"{base_name}.enex")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export.dtd">',
        f'<en-export export-date="{datetime.now().strftime("%Y%m%dT%H%M%SZ")}" application="AutoDork" version="1.0">',
    ]
    content_lines = [
        '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">',
        "<en-note>",
        f"<div><b>AutoDork Export</b> — {base_name}<br/>Exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
        "<ul>",
    ]
    for url, dorks in url_map.items():
        tag_line = ""
        if tags_map and url in tags_map and tags_map[url]:
            tag_line = f"<br/><i>Tags:</i> {', '.join(tags_map[url])}"
        content_lines.append(
            f'<li><a href="{url}">{url}</a><br/><i>Dorks:</i> {", ".join(dorks)}{tag_line}</li>'
        )
    content_lines.append("</ul>")
    content_lines.append(f"<div><b>Total URLs:</b> {len(url_map)}</div>")
    content_lines.append("</en-note>")
    content = "".join(content_lines)
    lines.append("<note>")
    lines.append(f"<title>{base_name}</title>")
    lines.append(f"<content><![CDATA[{content}]]></content>")
    lines.append(f"<created>{datetime.now().strftime('%Y%m%dT%H%M%SZ')}</created>")
    lines.append("<note-attributes/>")
    lines.append("</note>")
    lines.append("</en-export>")
    with open(enex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    console.print(f"[bold green]Exported Evernote ENEX:[/bold green] {enex_path}")
