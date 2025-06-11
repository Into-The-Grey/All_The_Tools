import os
import subprocess
import sys
import venv
import time
from colorama import Fore, Style, init

# === INIT COLOR OUTPUT ===
init(autoreset=True)

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
SCRIPT_PATH = os.path.join(BASE_DIR, "scripts")

# === STEP ORDER ===
STEPS = [
    "init_tag_files.py",
    "find_duplicates.py",
    "move_duplicates.py",
    "organize_by_date.py",
    "detect_nsfw.py",
    "smart_tag_images.py",
    "smart_tag_videos.py",
    "merge_tag_logs.py",
]

# === CREATE VENV ===
if not os.path.exists(VENV_DIR):
    print(Fore.CYAN + "🛠️  Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)

# === INSTALL DEPENDENCIES ===
print(Fore.CYAN + "📦 Installing dependencies from requirements.txt...")
subprocess.run(
    [PYTHON_EXEC, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL
)
subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "-r", REQUIREMENTS])

# === RUN SCRIPTS IN ORDER ===
for script in STEPS:
    script_path = os.path.join(SCRIPT_PATH, script)
    print(Fore.CYAN + f"\n🚀 Running {script}...")
    start_time = time.time()

    for attempt in range(1, 3):  # max 2 tries
        result = subprocess.run([PYTHON_EXEC, script_path])
        if result.returncode == 0:
            elapsed = time.time() - start_time
            print(
                Fore.GREEN
                + f"✅ {script} completed in {time.strftime('%H:%M:%S', time.gmtime(elapsed))}"
            )
            break
        else:
            if attempt == 1:
                print(Fore.YELLOW + f"⚠️  {script} failed on first attempt. Retrying...")
            else:
                print(Fore.RED + f"❌ {script} failed after retry. Aborting.")
                sys.exit(1)

print(Fore.GREEN + "\n🎉 All steps completed successfully.")
