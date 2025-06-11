# Media Organizer

## Automated, Offline Media Deduplication, Tagging, and Organization System

Clean up your messy image/video archive with a fully self-contained Python toolchain. This project detects and separates duplicates, organizes media by date, identifies NSFW content, applies intelligent tags using AI, and produces a complete searchable index.

---

## 🚀 Features

* 📦 **Exact Duplicate Detection**

  * MD5-based scanning to isolate true file-level duplicates

* 🧹 **Duplicate Management**

  * Retains one original; logs and moves all dupes to a `Duplicates/` folder

* 🗂️ **Date-Based Folder Organization**

  * Sorts media into `Organized/YYYY/MM/DD` using capture or modification date

* 🔞 **NSFW Detection (Offline)**

  * Detects unsafe content using [NudeNet](https://github.com/notAI-tech/NudeNet)
  * Moves NSFW files to `Tagged/NSFW`

* 🧠 **Smart AI Tagging**

  * Uses OpenAI CLIP via Hugging Face to label SFW media
  * Tag list auto-grows; you can manually edit or extend tag vocabularies

* 📄 **Search-Ready Indexing**

  * Outputs `media_index.jsonl` with path, tags, safety classification, and capture date

---

## 📁 Folder Structure

```bash
Media_Organizer/
├── main.py              # Master automation runner
├── requirements.txt     # All needed dependencies
├── README.md            # You're reading this
│
├── config/              # Controlled vocabularies (editable)
│   ├── tags_sfw.json
│   └── tags_nsfw.json
│
├── logs/                # Output logs and index
│   ├── duplicate_log.csv
│   ├── nsfw_log.csv
│   ├── media_tags.tsv
│   └── media_index.jsonl
│
├── scripts/             # Modular processing logic
│   ├── init_tag_files.py
│   ├── find_duplicates.py
│   ├── move_duplicates.py
│   ├── organize_by_date.py
│   ├── detect_nsfw.py
│   ├── smart_tag_images.py
│   └── build_media_index.py
│
├── Organized/           # Output: clean, date-organized library
├── Duplicates/          # Output: confirmed redundant files
├── Tagged/NSFW/         # Output: flagged unsafe content
└── venv/                # Local Python environment (auto-created)
```

---

## 🧠 How It Works (Flow Overview)

1. **Tag Initialization**

   * Creates and de-dupes basic tag vocabularies in `/config/`

2. **Duplicate Detection & Cleanup**

   * Detects identical files
   * Logs & moves extras to `Duplicates/`

3. **Chronological Sorting**

   * Extracts EXIF/metadata or fallback timestamps
   * Moves files into `/Organized/YYYY/MM/DD/`

4. **NSFW Classification**

   * Detects unsafe media
   * Moves flagged files to `Tagged/NSFW`

5. **Smart Tagging (CLIP)**

   * Labels remaining media using vision-language AI
   * Updates `/config/tags_sfw.json`
   * Logs results to `media_tags.tsv`

6. **Unified Index Build**

   * Aggregates all processed info into `media_index.jsonl`

---

## ⚙️ Usage

### 1. Install Python 3.8+

### 2. From inside the project folder

```bash
python main.py
```

* Automatically sets up a virtual environment
* Installs all dependencies
* Runs every step in sequence

---

## 🧩 Requirements

All dependencies are listed in `requirements.txt`:

```requirements.txt
transformers
torch
Pillow
pymediainfo
nudenet
```

Additional system requirement: [ffmpeg](https://ffmpeg.org/) for some video metadata.

---

## ✏️ Customization

* Add your own categories in `tags_sfw.json` or `tags_nsfw.json`
* Edit the `confidence threshold` in `smart_tag_images.py`
* Modify any script in `/scripts/` — each is modular and standalone

---

## 🛡️ Offline & Private

No internet calls are made during processing. Models run locally. Your data stays with you.

---

## 🧠 Credits

* OpenAI CLIP via Hugging Face
* NudeNet NSFW classifier
* `pymediainfo` for video metadata
* Pillow for image handling

---

## 🧰 Future Ideas

* Optional semantic tagging for NSFW content
* Face detection or scene clustering
* Tag-based search frontend or CLI query tool

---

**Built to give you back control over your chaotic archive.**

🖼️📽️📂💡
