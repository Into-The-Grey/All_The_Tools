# 🚀 AutoDork

![AutoDork Logo](../assets/AutoDork_logo.png)

![GitHub license](https://img.shields.io/github/license/Into-The-Grey/All_The_Tools?style=for-the-badge)

---

AutoDork is a modern, modular OSINT suite for automated Google dorking, username hunting, leak discovery, and threat reconnaissance. Designed for maximum flexibility and real-world workflow, AutoDork enables rapid investigations, repeatable research, and seamless export or reporting—while staying easy to extend and automate.

---

## 🌟 Features — In Depth

### 🧩 Modular Dork Scripts

* Swap, add, or edit Google dork modules instantly by dropping Python scripts into `scripts/`—no main.py edits required.
* Each dork module is self-describing: metadata, input prompts, and dork logic included. Build advanced queries for usernames, emails, phones, or custom targets.

### 🖥️ Rich CLI Workflow

* Interactive, colorized terminal menus for script selection, input entry, review, and tagging (powered by \[InquirerPy]).
* Visual output tables (with \[rich]) provide fast summaries, unique/deduped URL counts, and color-coded statuses.

### 🗃️ Bulk & Automation Modes

* Pass a wordlist to scan hundreds or thousands of targets at once.
* Use `--inputs key=value` for non-interactive, headless batch runs—ideal for automation and CI.
* Save your exact command and setup as a shell script or profile for later reuse, review, or audit.

### 💾 Results, Logging & Error Handling

* All sessions logged to `/logs/` with detailed error, progress, and result tracking.
* Results (deduped URLs by dork/query) output to `/results/` in JSON, CSV, HTML, and readable logs. Each run is timestamped, with full traceability.
* Optional caching skips previously-seen URLs for cleaner results.

### 🏷️ Review, Tag & Triage

* Tag URLs during review: label findings (leak, paste, profile, ignore, etc.) on the fly.
* Bulk tagging and search simplify triage of large sets for reports.
* All tag data is stored as JSON for downstream automation, workflow, or handoff.

### 🔁 Exports for Knowledgebases

* One-command export to:

  * **Obsidian** (Markdown: links, dorks, tags, stats)
  * **Notion** (Table markdown for import)
  * **Evernote** (ENEX XML)
* Exports live under `/exports/` and preserve tags/metadata.

### 🔐 Backup & Restore

* Single-command backup/restore for scripts and configs (to `/backups/` as zipped archives).
* Timestamped archives simplify transfer or rollback.

### 🛠️ Script Wizard

* Generate new dork modules with a guided wizard (no code needed): answer prompts, get a working script ready to customize.
* Multi-input, multi-query templates and custom prompts fully supported.

### 🏗️ Profile Management

* Save any workflow as a profile: capture script, config, inputs, and output options as a JSON profile.
* Load profiles instantly for recurring or team-based investigations.

### ⏲️ Scheduling & Automation

* Save your CLI run as a ready-to-use `.sh` script (for cron, automation, or documentation).
* Includes all CLI args, working directory, and config references.

---

## ⚡️ Installation & Quick Start

1. **Install dependencies (Python 3.12.x recommended):**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure dorks & settings:**

   * Edit `config/settings.yaml` to add/edit dorks, set result counts, blacklist domains, or choose output formats.
   * Drop scripts in `/scripts/` or run the wizard:

     ```bash
     python3 main.py --new-script
     ```

3. **Run interactively:**

   ```bash
   python3 main.py
   ```

   * Guided through script selection, input, review, tagging.

4. **Bulk/Automation:**

   ```bash
   python3 main.py --script username_dork.py --inputs username=jdoe --output json,csv
   # Or
   python3 main.py --script email_leak.py --wordlist my_emails.txt --quiet
   ```

5. **Exports:**

   ```bash
   python3 main.py --export-obsidian scriptname_username_TIMESTAMP
   python3 main.py --export-notion scriptname_username_TIMESTAMP
   python3 main.py --export-evernote scriptname_username_TIMESTAMP
   ```

   *`TIMESTAMP` = filename from `/results/`*

6. **Profiles & Schedules:**

   ```bash
   python3 main.py --save-profile my_search
   python3 main.py --load-profile my_search
   python3 main.py --save-schedule weekly_osint
   ```

7. **Backups:**

   ```bash
   python3 main.py --backup
   python3 main.py --list-backups
   python3 main.py --restore autodork_backup_YYYYMMDD_HHMMSS.zip
   ```

8. **Help/Usage Guide:**

   ```bash
   python3 utils/helpers/self_helper.py --more-help
   # Or see docs/usage_guide.md
   ```

---

## 🗂 Directory Structure

```bash
AutoDork/
├── main.py
├── config/
│   └── settings.yaml
├── scripts/
│   └── *.py
├── utils/
│   └── helpers/
│       ├── cache.py
│       ├── tag.py
│       ├── docgen.py
│       ├── backup.py
│       ├── export_obsidian.py
│       ├── export_evernote.py
│       ├── export_notion.py
│       ├── wizard.py
│       ├── bulk_tag.py
│       ├── schedule.py
│       ├── profile.py
│       └── self_helper.py
├── logs/
├── results/
├── backups/
├── profiles/
├── exports/
│   ├── obsidian/
│   ├── notion/
│   └── evernote/
├── assets/
│   └── AutoDork_logo.png
├── docs/
│   └── usage_guide.md
└── requirements.txt
```

---

## 📚 Example Use Cases

* **Username Threat Sweeps:** Feed a username into a dork script to surface forum mentions, password dumps, exposed profiles, and pastes across dozens of queries.
* **Bulk Email Exposure Checks:** Scan a wordlist of emails for public leaks or credential exposures.
* **Darkweb Leak Recon:** Extend with Tor dorks, or use profiles to automate/monitor leak sites over time.
* **Instant Reporting:** Tag and triage on the fly, export directly to Obsidian/Notion/Evernote, or backup for later review.
* **Red Team Recon:** Automate recon in CI/CD or via schedule scripts for continuous OSINT monitoring.

---

## 🛣 Roadmap

* Proxy & random User-Agent support
* API key integration (SerpAPI, Bing, etc.)
* Site-specific scraping & bypass
* Advanced workflow automation (chains, hooks)
* Web dashboard (future)

---

## ⚠️ Disclaimer

Use AutoDork responsibly. Respect privacy, legal boundaries, and terms of service.

---

## 📦 requirements.txt

```text
rich>=13.0.0
pyyaml>=6.0
jinja2>=3.0.0
InquirerPy>=0.3.4
googlesearch-python>=1.1.0
```

---

For further setup, full usage, and command reference, see [`docs/usage_guide.md`](docs/usage_guide.md) or run the Self Helper via CLI.
