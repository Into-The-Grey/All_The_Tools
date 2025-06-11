import os
import subprocess
import sys
import venv
import time
from colorama import Fore, Style, init

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
    # "detect_nsfw.py",  # ← NudeNet not currently compatible with Python 3.13; will re-enable when support is available.
    "smart_tag_images.py",
    "smart_tag_videos.py",
    "merge_tag_logs.py",
]

# === Step 4: Run scripts, skipping init_tag_files.py if tags exist ===
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
        except subprocess.CalledProcessError:
            print(
                Fore.RED
                + f"❌ {script} failed twice. Aborting pipeline."
                + Style.RESET_ALL
            )
            sys.exit(1)

print(Fore.GREEN + "\n🎉 All scripts completed successfully." + Style.RESET_ALL)

# --- Note for maintainers:
# To re-enable NSFW detection, uncomment 'detect_nsfw.py' in SCRIPTS when NudeNet
# supports Python 3.13+ (see README for details).
