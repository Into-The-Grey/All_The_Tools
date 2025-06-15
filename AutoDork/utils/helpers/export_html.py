import os
from jinja2 import Environment, FileSystemLoader


def export_html_report(base_name, url_map, results_dir, templates_dir, console):
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("html_report.j2")
    html = template.render(url_map=url_map)
    html_path = os.path.join(results_dir, f"{base_name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[bold green]Exported HTML report: {html_path}[/bold green]")
