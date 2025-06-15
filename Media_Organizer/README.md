# Media Organizer

![Media Organizer Logo](../assets/media_organizer_logo.png)

## Table of Contents

- [Media Organizer](#media-organizer)
  - [Table of Contents](#table-of-contents)
  - [Automated, Offline Media Deduplication, Tagging, and Organization System](#automated-offline-media-deduplication-tagging-and-organization-system)
  - [🚀 Features](#-features)
  - [🧠 How It Works](#-how-it-works)
  - [📁 Folder Structure](#-folder-structure)
  - [⚙️ Usage](#️-usage)
  - [📦 Requirements](#-requirements)
  - [✏️ Customization \& Power Tips](#️-customization--power-tips)
  - [🧰 Troubleshooting \& FAQ](#-troubleshooting--faq)
  - [🛡️ Privacy](#️-privacy)
  - [💡 Future Ideas](#-future-ideas)

## Automated, Offline Media Deduplication, Tagging, and Organization System

Take back your archive: **detects, sorts, tags, and indexes your photos & videos — 100% locally, offline, and private.**
No cloud. No vendor lock-in. Just pure Python, with serious power and polish.

---

## 🚀 Features

- **Exact Duplicate Detection**  
  MD5-based scan for byte-for-byte duplicates (even across folders)

- **Smart Duplicate Management**  
  One file kept; the rest are safely logged and moved to `/Duplicates/`

- **Date-Based Media Sorting**  
  Automatically organizes your media into `/Organized/YYYY/MM/DD/`  
  (Uses true capture date if available, not just modification time!)

- **Offline NSFW Detection (Auto-Backend!)**  
  *Works with either [NudeNet](https://github.com/notAI-tech/NudeNet) or [nsfw-detector](https://github.com/GantMan/nsfw_model)*

  - Python 3.8–3.12: Uses NudeNet or nsfw-detector
  - Python 3.13+: Uses conda environment (Python 3.12) for nsfw-detector
  - If both unavailable, step is skipped with a warning
  - All flagged files logged and available for review/search

- **AI-Powered Image & Video Tagging**  
  - Uses OpenAI CLIP (Hugging Face)
  - Adapts batch size and speed to your hardware (CUDA, CPU, RAM)
  - Auto-updates your tag vocabularies; manual editing supported

- **Unified Searchable Index**  
  Combines tags, NSFW status, capture time, and more in `media_index.jsonl` for easy auditing or scripting

- **Colorful, User-Friendly Pipeline**  
  - Pipeline-level progress bar + step-by-step color logs
  - Time tracking and graceful auto-retry
  - DRY RUN support for safe experimentation

---

## 🧠 How It Works

1. **Initialize Tag Files:**  
   Creates/reuses `/config/tags_sfw.json` & `/config/tags_nsfw.json`.

2. **Find and Log Duplicates:**  
   MD5-hashes all media, finds perfect matches, moves extra copies to `/Duplicates/`.

3. **Organize by Date:**  
   Reads EXIF/video metadata; sorts everything into `/Organized/YYYY/MM/DD/`.

4. **NSFW Detection:**  
   Runs in a dedicated Python 3.12 conda env with `nsfw-detector` if needed (auto-managed).  
   Logs and (optionally) moves unsafe files.

5. **AI Smart Tagging:**  
   Images and video frames are labeled using CLIP; new tags added to vocabularies.

6. **Unified Index:**  
   All metadata, tags, and NSFW results are merged into a fast-searchable `.jsonl` file.

---

## 📁 Folder Structure

```bash
Media_Organizer/
├── main.py
├── requirements.txt
├── nsfw_env.yml
├── README.md
│
├── config/
│   ├── tags_sfw.json
│   └── tags_nsfw.json
│
├── logs/
│   ├── duplicate_log_*.csv
│   ├── nsfw_log_*.csv
│   ├── media_tags_*.tsv
│   ├── video_tags_*.tsv
│   ├── media_index_*.jsonl
│   └── *_errors_*.log
│
├── scripts/
│   ├── init_tag_files.py
│   ├── find_duplicates.py
│   ├── move_duplicates.py
│   ├── organize_by_date.py
│   ├── detect_nsfw.py
│   ├── smart_tag_images.py
│   ├── smart_tag_videos.py
│   └── merge_tag_logs.py
│
├── Organized/
├── Duplicates/
├── Tagged/NSFW/
└── venv/
````

---

## ⚙️ Usage

1. **Install Python 3.8–3.13** (Windows/Linux/MacOS)
2. **From inside your project folder:**

```bash
python main.py
```

- Auto-creates a `venv/` and installs everything for the main pipeline.
- When needed, auto-installs Miniconda and creates a special conda env for NSFW detection (`nsfw_env.yml`).
- Guides you with prompts and color logs.
- Progress bars show both step-level and pipeline-wide progress.
- DRY RUN mode available on all scripts for no-risk testing.

---

## 📦 Requirements

- **requirements.txt** (core pipeline):

  ```text
  torch
  transformers
  tqdm
  colorama
  Pillow
  opencv-python
  pymediainfo
  pyyaml
  ```

- **nsfw\_env.yml** (for the NSFW conda environment):

  ```yaml
  name: mediaorg_py312
  channels:
    - defaults
  dependencies:
    - python=3.12
    - tensorflow
    - nsfw-detector
    - pillow
    - tqdm
    - colorama
  ```

  *If you have trouble installing `nsfw-detector`, make sure Miniconda is being used and `pip` is available in the environment. See [nsfw-detector PyPI page](https://pypi.org/project/nsfw-detector/) for any 3.12+ issues.*

*Optional: [FFmpeg](https://ffmpeg.org/) in your PATH is highly recommended for best video support.*

---

## ✏️ Customization & Power Tips

- **Edit `/config/tags_sfw.json` and `/config/tags_nsfw.json`** to tailor your tagging
- **Adjust thresholds** (`confidence_threshold`, `batch_size`, etc.) in `config.json` for performance tuning
- **Resume and checkpoints**: all steps support `--resume` after interruption
- **Error logs** in `/logs/` show everything that couldn’t be processed, for easy troubleshooting

---

## 🧰 Troubleshooting & FAQ

- **NSFW detection “skipped”?**

  - You may be on Python 3.13+ with no working backend.
  - The pipeline will auto-create and use a conda env if possible, but if no backend is available, NSFW is skipped with a warning.

- **CUDA not used?**

  - Make sure you have [CUDA installed](https://developer.nvidia.com/cuda-downloads) and `torch` built for your GPU.

- **Script failed mid-pipeline?**

  - Just rerun `main.py` and use `--resume` on failed steps.
  - Check `/logs/*_errors_*.log` for details.

---

## 🛡️ Privacy

- **No internet required after setup**
- **All AI runs locally**
- **No data leaves your computer**

---

## 💡 Future Ideas

- Tag-based CLI search and filtering tools
- Scene/face clustering
- File integrity repair and partial recovery
- Super-fast parallel processing for giant archives

---

**Built for power-users, by power-users.**
🖼️📽️🧠🔍 Control your data, don’t let your data control you.

---

**Ready to run? `python main.py` and watch the chaos become order.**
