import os
import sys

HELP_TEXT = """
AutoDork — Self Help

This tool is for direct questions about AutoDork’s capabilities, feature quick-tips, and troubleshooting.  
For the full usage guide, run:

    python3 main.py --more-help

Or see the markdown doc in the /docs folder.
---
Quick commands:
- Use --list-templates to see available dork scripts.
- Use --new-script to launch the script creation wizard.
- Use --backup / --restore for config and script backups.
- Use --tag-bulk BASE_NAME for bulk tagging of results.
- Use --export-obsidian BASE_NAME, --export-notion BASE_NAME, --export-evernote BASE_NAME for data exports.
- Use --save-profile / --load-profile to manage sets of settings.
- Use --save-schedule NAME to export a bash script for cron/automation.

See docs/UsageGuide.md for more.
"""


def print_self_help(console):
    console.print(HELP_TEXT)


def open_usage_guide(base, console):
    guide_path = os.path.join(base, "docs", "UsageGuide.md")
    if os.path.exists(guide_path):
        # Try to open with less, fallback to cat
        try:
            os.system(f"less '{guide_path}' || cat '{guide_path}'")
        except Exception:
            with open(guide_path, "r", encoding="utf-8") as f:
                console.print(f.read())
    else:
        console.print(f"[red]Usage guide not found at {guide_path}[/red]")
