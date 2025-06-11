import os
import subprocess
import sys
import venv

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
SCRIPT_PATH = os.path.join(BASE_DIR, "scripts")

# === Step 1: Setup virtual environment ===
if not os.path.exists(VENV_DIR):
    print("🛠️ Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)

# === Step 2: Install requirements ===
print("📦 Installing dependencies...")
subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "-r", REQUIREMENTS])

# === Step 3: Run scripts in order ===
STEPS = [
    "init_tag_files.py",
    "find_duplicates.py",
    "move_duplicates.py",
    "organize_by_date.py",
    "detect_nsfw.py",
    "smart_tag_images.py",
    "build_media_index.py",
]

for script in STEPS:
    script_path = os.path.join(SCRIPT_PATH, script)
    print(f"\n🚀 Running {script}")
    result = subprocess.run([PYTHON_EXEC, script_path])
    if result.returncode != 0:
        print(f"❌ Error in {script}, aborting.")
        sys.exit(1)

print("\n✅ All processing complete.")
