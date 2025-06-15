# AutoDork Usage Guide

Welcome to **AutoDork** – an automated Google Dorking suite for offensive OSINT, reporting, and export.  
This guide explains every major feature, CLI argument, helper module, and output format.

---

## Getting Started

- **Run the tool:**  

  ```bash
  python3 main.py
    ```

This will launch interactive mode, allowing you to select a dork script and enter your inputs.

 **Help:**

  ```bash
  python3 main.py --more-help
  ```

  (Opens this usage guide.)

---

## Command-Line Arguments

| Argument            | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `--script`          | Script filename or name from `scripts/`                             |
| `--inputs`          | CLI inputs as `key=value` pairs (for automation/bulk)               |
| `--wordlist`        | File with one input per line (bulk mode)                            |
| `--output`          | Comma-separated output formats: `json,csv,html,log`                 |
| `--quiet`           | Automation mode (no interactive prompts)                            |
| `--edit-templates`  | Edit a dork script with your default `$EDITOR`                      |
| `--list-templates`  | List all available dork script templates                            |
| `--generate-docs`   | Generate markdown documentation for all dork scripts                |
| `--backup`          | Backup all `config/` and `scripts/`                                 |
| `--restore`         | Restore a backup by filename                                        |
| `--list-backups`    | List all available backups                                          |
| `--export-obsidian` | Export results as Markdown for Obsidian (provide results base name) |
| `--export-evernote` | Export results as ENEX for Evernote (provide base name)             |
| `--export-notion`   | Export results as Markdown for Notion (provide base name)           |
| `--new-script`      | Launch the dork script creation wizard                              |
| `--tag-bulk`        | Tag all URLs in a result set (provide base name)                    |
| `--save-schedule`   | Save your current CLI command as a `.sh` script for cron/automation |
| `--save-profile`    | Save your current config/args as a named profile                    |
| `--load-profile`    | Load config/args from a named profile                               |
| `--more-help`       | Show this usage guide                                               |

---

## Workflow Overview

### 1. Script Discovery & Selection

- Dork scripts are loaded from `/scripts/` and can be selected via fuzzy search.
- Each script provides its own inputs and prompt texts.

### 2. Input Collection

- Interactive prompts or CLI/wordlist inputs.
- Bulk mode supported for large-scale recon.

### 3. Dork Execution

- Dorks are run with optional progress bars.
- Each found URL is deduplicated, cached, and attributed to the dork that discovered it.
- Supports blacklist domains via config.

### 4. Output

- Results are saved in `/results/` in all specified formats.
- Optional HTML report template used from `utils/templates/results_template.html`.

### 5. Review & Tagging

- Interactive review to select URLs for follow-up.
- Tag each URL with presets or custom tags.
- Tagged data is saved to `followup_tags.json`.

---

## Export Helpers

- **Obsidian:** Markdown summary, per-URL dorks/tags, to `/exports/obsidian/`.
- **Evernote:** ENEX XML, structured for Evernote import, to `/exports/evernote/`.
- **Notion:** Markdown with table layout, to `/exports/notion/`.

---

## Backup & Restore

- **Backup:**
  Creates timestamped `.zip` files in `/backups/` containing `config/` and `scripts/`.
- **Restore:**
  Interactive confirmation; restores files from selected backup.

---

## Script Creation Wizard

- Launch via `--new-script`
- Wizard collects:

  - Name, filename, description
  - Number of inputs and their prompts
  - Dork template(s) (can use Python `.format()` variables)
- Generates a `.py` script under `/scripts/`.

---

## Profiles & Automation

- **Profiles:**
  Save/restore all inputs, configs, script name, wordlist, and outputs for repeatable runs.
- **Schedule:**
  Save the exact CLI as a `.sh` script to `/schedules/` for use in cron jobs or automation.

---

## Bulk Tagging

- Apply tags to every URL in a results JSON, fast and interactively.
- Tags stored in `/results/followup_tags.json`.

---

## Usage Examples

- **Run interactively:**

  ```bash
  python3 main.py
  ```

- **Bulk scan usernames from a wordlist:**

  ```bash
  python3 main.py --script username_dork.py --wordlist usernames.txt --output json,csv,html
  ```

- **Automation (no prompts):**

  ```bash
  python3 main.py --script email_dork.py --inputs email=foo@bar.com --quiet --output csv
  ```

- **Export Obsidian Markdown:**

  ```bash
  python3 main.py --export-obsidian username_dork_foo_1718608956
  ```

- **Create backup:**

  ```bash
  python3 main.py --backup
  ```

- **Restore from backup:**

  ```bash
  python3 main.py --restore autodork_backup_20240616_112301.zip
  ```

---

## Helper Modules Breakdown

**Location:** `utils/helpers/`

| Helper File          | Description                                        |
| -------------------- | -------------------------------------------------- |
| `cache.py`           | Load/save URL cache                                |
| `tag.py`             | Interactive tagging and bulk tagging helpers       |
| `docgen.py`          | Dork script Markdown doc generator                 |
| `backup.py`          | Backup, list, and restore configs/scripts          |
| `export_obsidian.py` | Markdown export to `/exports/obsidian/`            |
| `export_evernote.py` | ENEX export to `/exports/evernote/`                |
| `export_notion.py`   | Markdown table export to `/exports/notion/`        |
| `wizard.py`          | Dork script creation wizard (interactive)          |
| `bulk_tag.py`        | Bulk tag results with presets and custom tags      |
| `schedule.py`        | Save CLI args as `.sh` scripts for cron/automation |
| `profile.py`         | Save/load complete config and CLI profile          |
| `self_helper.py`     | Self-help and `--more-help` doc handling           |

**Templates:**

- HTML report template at `utils/templates/results_template.html` (used for HTML output format).

---

## Advanced Usage

- All helpers are fully modular and can be called standalone.
- Add your own dork scripts under `/scripts/` following the metadata/generate\_dorks pattern.
- Extend exports by copying the export helpers and adjusting for your system.

---

## Troubleshooting

- Errors and failed dork runs are logged to `/logs/errors.log`.
- If a helper or script is missing, check your folder tree matches the guide above.
- For maximum flexibility, use profiles and schedule scripts for all repeat runs.

---

## Contributing

- Add new helpers or exports in `/utils/helpers/`.
- Keep your folder structure consistent; never mix outputs with code.
- Share new dork scripts with detailed input prompts and docstrings!

---

*Made with ❤️ for power users. For more details, see the source and the helper docstrings.*

---
