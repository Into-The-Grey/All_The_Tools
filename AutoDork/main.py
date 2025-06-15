import os
import sys
import importlib.util
import argparse
import time
import random
import yaml
import json
import csv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import track
from InquirerPy import inquirer  # type: ignore
from googlesearch import search  # type: ignore
from jinja2 import Environment, FileSystemLoader

# --- Helper imports ---
from utils.helpers.cache import load_url_cache, save_url_cache
from utils.helpers.tag import tag_urls
from utils.helpers.docgen import generate_docs
from utils.helpers.backup import (
    backup_configs_and_scripts,
    list_backups,
    restore_backup,
)
from utils.helpers.export_obsidian import export_to_obsidian
from utils.helpers.export_evernote import export_to_evernote
from utils.helpers.export_notion import export_to_notion
from utils.helpers.wizard import new_script_wizard
from utils.helpers.bulk_tag import bulk_tag_urls
from utils.helpers.schedule import save_schedule_script
from utils.helpers.profile import save_profile, load_profile
from utils.helpers.self_helper import print_self_help, open_usage_guide

console = Console()
BASE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(BASE, "logs")
RESULTS = os.path.join(BASE, "results")
SCRIPTS_DIR = os.path.join(BASE, "scripts")
CONFIG_DIR = os.path.join(BASE, "config")
BACKUPS = os.path.join(BASE, "backups")
EXPORTS = os.path.join(BASE, "exports")
os.makedirs(LOGS, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(BACKUPS, exist_ok=True)
os.makedirs(EXPORTS, exist_ok=True)

CACHE_FILE = os.path.join(RESULTS, "url_cache.json")


def load_config():
    config_path = os.path.join(CONFIG_DIR, "settings.yaml")
    if not os.path.exists(config_path):
        console.print(
            f"[bold red]ERROR:[/bold red] Config file {config_path} not found!"
        )
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def discover_scripts():
    dork_scripts = []
    for fname in os.listdir(SCRIPTS_DIR):
        if fname.endswith(".py"):
            path = os.path.join(SCRIPTS_DIR, fname)
            name = fname[:-3]
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                console.print(f"[red]Failed to load {fname}: Invalid module spec[/red]")
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                meta = mod.get_metadata()
                dork_scripts.append(
                    {
                        "name": meta["name"],
                        "description": meta["description"],
                        "inputs": meta["inputs"],
                        "module": mod,
                        "filename": fname,
                    }
                )
            except Exception as e:
                console.print(f"[red]Failed to load {fname}: {e}[/red]")
    return dork_scripts


def prompt_script(scripts):
    choices = [
        f'{i+1}. {s["name"]} — {s["description"]}' for i, s in enumerate(scripts)
    ]
    idx = inquirer.fuzzy(message="Select a dork script:", choices=choices).execute()
    selected_idx = choices.index(idx)
    return scripts[selected_idx]


def prompt_inputs(inputs_meta, cli_inputs=None, quiet=False):
    user_inputs = {}
    for inp in inputs_meta:
        key = inp["name"]
        if cli_inputs and key in cli_inputs:
            user_inputs[key] = cli_inputs[key]
        elif quiet:
            raise Exception(f"Missing required input '{key}' for quiet mode.")
        else:
            user_inputs[key] = inquirer.text(message=inp["prompt"]).execute()
    return user_inputs


def run_dorks(
    dorks, num_results, delay_min, delay_max, blacklist, progress=True, url_cache=None
):
    results = {}
    url_map = {}
    errors = []
    seen_urls = url_cache or set()
    new_urls_this_run = set()
    dorks_iter = track(dorks, description="Running dorks...") if progress else dorks
    for dork in dorks_iter:
        urls = []
        console.print(f"[bold blue][DORK][/bold blue] {dork}")
        try:
            for url in search(dork, num_results=num_results, lang="en"):
                if any(domain in url for domain in blacklist):
                    continue
                if url not in url_map:
                    if url not in seen_urls:
                        console.print(f"  [green][NEW][/green] {url}")
                        new_urls_this_run.add(url)
                    else:
                        console.print(f"  [yellow][SEEN][/yellow] {url}")
                else:
                    console.print(f"  [grey58][DUP][/grey58] {url}")
                urls.append(url)
                url_map.setdefault(url, []).append(dork)
            if not urls:
                console.print("   [yellow]No results found[/yellow]")
        except Exception as e:
            err_msg = f"{dork}: {e}"
            errors.append(err_msg)
            with open(os.path.join(LOGS, "errors.log"), "a") as errlog:
                errlog.write(f"{datetime.now()} - {err_msg}\n")
            console.print(f"  [red][!][/red] Error: {e}")
        results[dork] = urls
        time.sleep(random.uniform(delay_min, delay_max))
    return results, url_map, errors, new_urls_this_run


def write_outputs(base_name, results, url_map, output_formats):
    if "log" in output_formats:
        log_path = os.path.join(LOGS, f"{base_name}.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for dork, urls in results.items():
                f.write(f"Dork: {dork}\n")
                for url in urls:
                    f.write(f"    {url}\n")
                f.write("\n")
    if "json" in output_formats:
        json_path = os.path.join(RESULTS, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(url_map, jf, indent=2)
    if "csv" in output_formats:
        csv_path = os.path.join(RESULTS, f"{base_name}.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Found By Dork(s)"])
            for url, dorks in url_map.items():
                writer.writerow([url, "; ".join(dorks)])
    if "html" in output_formats:
        html_template_path = os.path.join(
            BASE, "utils", "templates", "results_template.html"
        )
        if os.path.exists(html_template_path):
            with open(html_template_path, "r", encoding="utf-8") as tplf:
                html_template = tplf.read()
        else:
            # fallback (should rarely ever be used)
            html_template = """
            <!DOCTYPE html>
            <html><head><title>AutoDork Results</title></head>
            <body>
            <h1>AutoDork Results</h1>
            <table border=1>
            <tr><th>URL</th><th>Dorks</th></tr>
            {% for url, dorks in url_map.items() %}
                <tr>
                    <td><a href="{{ url }}">{{ url }}</a></td>
                    <td>{{ ", ".join(dorks) }}</td>
                </tr>
            {% endfor %}
            </table>
            </body></html>
            """
        env = Environment()
        template = env.from_string(html_template)
        html = template.render(url_map=url_map)
        html_path = os.path.join(RESULTS, f"{base_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)


def show_summary(results, url_map):
    table = Table(title="AutoDork Summary")
    table.add_column("Dork", style="cyan", overflow="fold")
    table.add_column("Hits", justify="right", style="green")
    for dork, urls in results.items():
        table.add_row(dork, str(len(urls)))
    console.print(table)
    total_unique = len(url_map)
    total_hits = sum(len(u) for u in results.values())
    console.print(f"[bold cyan]Total unique URLs:[/bold cyan] {total_unique}")
    console.print(f"[bold cyan]Total hits (incl. duplicates):[/bold cyan] {total_hits}")


def interactive_review(url_map):
    urls = list(url_map.keys())
    if not urls:
        console.print("[yellow]No URLs found for review.[/yellow]")
        return []
    chosen = inquirer.checkbox(
        message="Mark URLs for follow-up (space = select):", choices=urls
    ).execute()
    if chosen:
        with open(os.path.join(RESULTS, "followup.txt"), "w", encoding="utf-8") as f:
            for url in chosen:
                f.write(url + "\n")
        console.print(f"[green]Saved marked URLs to results/followup.txt[/green]")
        console.print(
            "[bold cyan]Tag your marked URLs (optional, enter to skip any):[/bold cyan]"
        )
        tags = tag_urls(chosen)
        tag_path = os.path.join(RESULTS, "followup_tags.json")
        with open(tag_path, "w", encoding="utf-8") as tf:
            json.dump(tags, tf, indent=2)
        console.print(f"[cyan]Saved tags to {tag_path}[/cyan]")
    return chosen


def edit_templates(scripts):
    choices = [f'{i+1}. {s["filename"]}: {s["name"]}' for i, s in enumerate(scripts)]
    idx = inquirer.select(
        message="Select a dork script to edit:", choices=choices + ["Cancel"]
    ).execute()
    if idx == "Cancel":
        return
    selected = scripts[choices.index(idx)]
    fname = os.path.join(SCRIPTS_DIR, selected["filename"])
    editor = os.environ.get("EDITOR", "nano")
    os.system(f"{editor} '{fname}'")
    console.print(f"[yellow]Reload or restart to see changes.[/yellow]")


def list_templates(scripts):
    table = Table(title="Dork Script Templates")
    table.add_column("Filename")
    table.add_column("Name")
    table.add_column("Description")
    for s in scripts:
        table.add_row(s["filename"], s["name"], s["description"])
    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="AutoDork: Automated Google Dorking Tool (modular edition)"
    )
    parser.add_argument(
        "--script",
        type=str,
        help="Script filename from scripts/ (e.g., username_dork.py)",
    )
    parser.add_argument(
        "--inputs", nargs="*", help="Input(s) as key=value pairs for automation mode"
    )
    parser.add_argument(
        "--wordlist", type=str, help="File containing one input per line for bulk mode"
    )
    parser.add_argument("--output", type=str, help="Comma-separated: json,csv,html,log")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="No interactive prompts, for automation use",
    )
    parser.add_argument(
        "--edit-templates", action="store_true", help="Open template file editor"
    )
    parser.add_argument(
        "--list-templates", action="store_true", help="List available dork templates"
    )
    parser.add_argument(
        "--generate-docs",
        action="store_true",
        help="Generate Markdown docs for all dork scripts",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Backup config/ and scripts/ folders"
    )
    parser.add_argument(
        "--restore",
        type=str,
        help="Restore config/scripts from backup (provide backup filename)",
    )
    parser.add_argument(
        "--list-backups", action="store_true", help="List available backups"
    )
    parser.add_argument(
        "--export-obsidian",
        type=str,
        help="Export results as Markdown for Obsidian (provide results base name)",
    )
    parser.add_argument(
        "--export-evernote",
        type=str,
        help="Export results to Evernote ENEX (provide base name)",
    )
    parser.add_argument(
        "--export-notion",
        type=str,
        help="Export results as Markdown for Notion (provide base name)",
    )
    parser.add_argument(
        "--new-script",
        action="store_true",
        help="Wizard: Create a new dork script template",
    )
    parser.add_argument(
        "--tag-bulk", type=str, help="Tag all URLs in a result file (provide base name)"
    )
    parser.add_argument(
        "--save-schedule",
        type=str,
        help="Save current CLI args as a .sh script (provide a name for the script)",
    )
    parser.add_argument(
        "--save-profile",
        type=str,
        help="Save current config/args as a profile (provide profile name)",
    )
    parser.add_argument(
        "--load-profile",
        type=str,
        help="Load config/args from a profile (provide profile name)",
    )
    parser.add_argument(
        "--more-help", action="store_true", help="Show advanced usage guide"
    )

    args = parser.parse_args()

    if args.more_help:
        open_usage_guide(BASE, console)
        sys.exit(0)
    if args.new_script:
        new_script_wizard(SCRIPTS_DIR, console, inquirer)
        sys.exit(0)
    if args.save_schedule:
        save_schedule_script(args.save_schedule, sys.argv, BASE, console)
        sys.exit(0)

    config = load_config()
    dork_scripts = discover_scripts()
    if args.list_templates:
        list_templates(dork_scripts)
        sys.exit(0)
    if args.edit_templates:
        edit_templates(dork_scripts)
        sys.exit(0)
    if args.generate_docs:
        generate_docs(dork_scripts, BASE, console)
        sys.exit(0)
    if args.backup:
        backup_configs_and_scripts(CONFIG_DIR, SCRIPTS_DIR, BACKUPS, BASE, console)
        sys.exit(0)
    if args.list_backups:
        list_backups(BACKUPS, console)
        sys.exit(0)
    if args.restore:
        restore_backup(args.restore, BACKUPS, BASE, console, inquirer)
        sys.exit(0)
    if args.tag_bulk:
        bulk_tag_urls(args.tag_bulk, RESULTS, tag_urls, console)
        sys.exit(0)

    # EXPORTS BLOCK
    if args.export_obsidian or args.export_evernote or args.export_notion:
        base_name = args.export_obsidian or args.export_evernote or args.export_notion
        json_path = os.path.join(RESULTS, f"{base_name}.json")
        tag_path = os.path.join(RESULTS, "followup_tags.json")
        if not os.path.exists(json_path):
            console.print(f"[red]Results file {json_path} not found![/red]")
            sys.exit(1)
        with open(json_path, "r", encoding="utf-8") as jf:
            url_map = json.load(jf)
        tags_map = {}
        if os.path.exists(tag_path):
            with open(tag_path, "r", encoding="utf-8") as tf:
                tags_map = json.load(tf)
        if args.export_obsidian:
            export_to_obsidian(base_name, url_map, tags_map, BASE, console)
            sys.exit(0)
        if args.export_evernote:
            export_to_evernote(base_name, url_map, tags_map, BASE, console)
            sys.exit(0)
        if args.export_notion:
            export_to_notion(base_name, url_map, tags_map, BASE, console)
            sys.exit(0)

    # -- Profile Save/Load --
    cli_inputs = {}
    if args.inputs:
        for i in args.inputs:
            if "=" in i:
                k, v = i.split("=", 1)
                cli_inputs[k] = v
    if args.load_profile:
        pf = load_profile(args.load_profile, BASE, console)
        if pf:
            cli_inputs = pf["cli_inputs"]
            config = pf["config"]
            args.script = pf["script"]
            args.wordlist = pf["wordlist"]
            args.output = pf["output"]
    if args.save_profile:
        save_profile(
            args.save_profile,
            cli_inputs,
            config,
            args.script,
            args.wordlist,
            args.output,
            BASE,
            console,
        )
        sys.exit(0)

    num_results = config.get("num_results", 8)
    delay_min = config.get("delay_min", 2)
    delay_max = config.get("delay_max", 5)
    blacklist = config.get("blacklist", [])
    output_formats = [
        x.strip()
        for x in (args.output or ",".join(config.get("output_formats", ["log"]))).split(
            ","
        )
    ]

    selected = None
    if args.script:
        found = [
            s
            for s in dork_scripts
            if s["filename"] == args.script or s["name"] == args.script
        ]
        if not found:
            console.print(f"[red]Script {args.script} not found![/red]")
            sys.exit(1)
        selected = found[0]
    elif args.quiet:
        console.print("[red]You must specify --script in quiet mode![/red]")
        sys.exit(1)
    else:
        selected = prompt_script(dork_scripts)

    bulk_targets = []
    if args.wordlist:
        with open(args.wordlist) as f:
            bulk_targets = [line.strip() for line in f if line.strip()]
    else:
        bulk_targets = [None]

    url_cache = load_url_cache(CACHE_FILE)
    for idx, target in enumerate(bulk_targets):
        this_inputs = cli_inputs.copy()
        if target is not None:
            primary_key = (
                selected["inputs"][0]["name"] if selected["inputs"] else "input"
            )
            this_inputs[primary_key] = target
        try:
            user_inputs = prompt_inputs(
                selected["inputs"], cli_inputs=this_inputs, quiet=args.quiet
            )
        except Exception as e:
            console.print(f"[red]Input error: {e}[/red]")
            continue
        dorks = selected["module"].generate_dorks(user_inputs)
        base_name = f"{selected['filename'].replace('.py','')}_{user_inputs.get(selected['inputs'][0]['name'],'run')}_{int(time.time())}"
        results, url_map, errors, new_urls_this_run = run_dorks(
            dorks,
            num_results,
            delay_min,
            delay_max,
            blacklist,
            progress=(not args.quiet),
            url_cache=url_cache,
        )
        write_outputs(base_name, results, url_map, output_formats)
        show_summary(results, url_map)
        if not args.quiet:
            interactive_review(url_map)
        if new_urls_this_run:
            save_url_cache(list(url_cache | new_urls_this_run), CACHE_FILE)
            url_cache |= new_urls_this_run
            console.print(
                f"[bold green]Added {len(new_urls_this_run)} new URLs to cache.[/bold green]"
            )
        else:
            console.print(f"[cyan]No new URLs found in this run.[/cyan]")
        console.print(
            f"[green]Results for '{base_name}' saved to results/ and logs/[/green]\n"
        )


if __name__ == "__main__":
    main()
