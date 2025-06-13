import os
import subprocess
import sys
import venv
import time
from colorama import Fore, Style, init
from tqdm import tqdm  # Add at the top

# Initialize color output
init(autoreset=True)

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
SCRIPT_PATH = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(BASE_DIR, "config")

# === Prompt user for media directory ONCE ===
input_path = input(
    "📁 Enter the absolute path to your media directory (read-only): "
).strip()
if not os.path.isdir(input_path):
    print(
        Fore.RED
        + f"[ERROR] The provided path is not valid: {input_path}"
        + Style.RESET_ALL
    )
    sys.exit(1)

# === Step 1: Setup virtual environment ===
if not os.path.exists(VENV_DIR):
    print(Fore.CYAN + "🛠️ Creating virtual environment..." + Style.RESET_ALL)
    venv.create(VENV_DIR, with_pip=True)

# === Step 2: Install requirements ===
print(Fore.CYAN + "📦 Installing dependencies..." + Style.RESET_ALL)
subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "-r", REQUIREMENTS])

# === Step 3: Define scripts in order ===
SCRIPTS = [
    "init_tag_files.py",
    "find_duplicates.py",
    "move_duplicates.py",
    "organize_by_date.py",
    "detect_nsfw.py",  # Now auto-handles backend support and skips if unavailable
    "smart_tag_images.py",
    "smart_tag_videos.py",
    "merge_tag_logs.py",
]

# === Step 4: Determine total steps (skip if tags exist) ===
effective_scripts = []
for script in SCRIPTS:
    if script == "init_tag_files.py":
        sfw_tags = os.path.join(CONFIG_PATH, "tags_sfw.json")
        nsfw_tags = os.path.join(CONFIG_PATH, "tags_nsfw.json")
        if os.path.isfile(sfw_tags) and os.path.isfile(nsfw_tags):
            continue
    effective_scripts.append(script)

# --- Total progress bar ---
total_steps = len(effective_scripts)
print(Fore.MAGENTA + f"\nPipeline: {total_steps} steps to run." + Style.RESET_ALL)
pipeline_pbar = tqdm(total=total_steps, desc="📊 Pipeline Progress", colour="magenta")

# === Step 5: Run scripts, skipping as needed ===
for script in SCRIPTS:
    if script == "init_tag_files.py":
        sfw_tags = os.path.join(CONFIG_PATH, "tags_sfw.json")
        nsfw_tags = os.path.join(CONFIG_PATH, "tags_nsfw.json")
        if os.path.isfile(sfw_tags) and os.path.isfile(nsfw_tags):
            print(
                Fore.GREEN
                + "✅ Tag files already exist. Skipping init_tag_files.py."
                + Style.RESET_ALL
            )
            continue

    script_path = os.path.join(SCRIPT_PATH, script)
    print(Fore.CYAN + f"\n🚀 Running: {script}" + Style.RESET_ALL)
    start = time.time()

    try:
        result = subprocess.run([PYTHON_EXEC, script_path, input_path], check=True)
        duration = time.time() - start
        print(
            Fore.GREEN
            + f"✅ Completed {script} in {int(duration)} seconds."
            + Style.RESET_ALL
        )
        pipeline_pbar.update(1)  # <--- Update total progress bar on script success
    except subprocess.CalledProcessError:
        print(Fore.YELLOW + f"⚠️ {script} failed. Retrying once..." + Style.RESET_ALL)
        try:
            result = subprocess.run([PYTHON_EXEC, script_path, input_path], check=True)
            duration = time.time() - start
            print(
                Fore.GREEN
                + f"✅ Retry succeeded for {script} in {int(duration)} seconds."
                + Style.RESET_ALL
            )
            pipeline_pbar.update(1)  # Update if success on retry
        except subprocess.CalledProcessError:
            print(
                Fore.RED
                + f"❌ {script} failed twice. Aborting pipeline."
                + Style.RESET_ALL
            )
            pipeline_pbar.close()
            sys.exit(1)

pipeline_pbar.close()
print(Fore.GREEN + "\n🎉 All scripts completed successfully." + Style.RESET_ALL)
