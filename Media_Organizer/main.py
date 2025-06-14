import os
import subprocess
import sys
import venv
import time
from colorama import Fore, Style, init
from tqdm import tqdm

# Initialize color output
init(autoreset=True)

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON_EXEC = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
SCRIPT_PATH = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(BASE_DIR, "config")
NSFW_ENV_YML = os.path.join(BASE_DIR, "nsfw_env.yml")
TEMP_REQS = os.path.join(BASE_DIR, "requirements_main.txt")


def run_detect_nsfw_conda(input_path):
    conda_env_name = "mediaorg_py312"
    miniconda_installer = "Miniconda3-latest-Linux-x86_64.sh"
    home_dir = os.path.expanduser("~")
    conda_dir = os.path.join(home_dir, "miniconda3")
    env_python = os.path.join(conda_dir, "envs", conda_env_name, "bin", "python")
    script_path = os.path.join(SCRIPT_PATH, "detect_nsfw.py")

    # Step 1: Install Miniconda if needed
    if not os.path.exists(conda_dir):
        print(
            Fore.CYAN + "🔧 Downloading and installing Miniconda..." + Style.RESET_ALL
        )
        subprocess.run(
            f"wget https://repo.anaconda.com/miniconda/{miniconda_installer} -O /tmp/{miniconda_installer}",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"bash /tmp/{miniconda_installer} -b -p {conda_dir}", shell=True, check=True
        )
        subprocess.run(f"{conda_dir}/bin/conda init", shell=True, check=True)

    # Step 2: Create env from YML if missing
    envs = subprocess.check_output([f"{conda_dir}/bin/conda", "env", "list"]).decode()
    if conda_env_name not in envs:
        print(
            Fore.CYAN
            + f"🔧 Creating conda env {conda_env_name} from nsfw_env.yml..."
            + Style.RESET_ALL
        )
        subprocess.run(
            [f"{conda_dir}/bin/conda", "env", "create", "-f", NSFW_ENV_YML], check=True
        )

    # Step 3: Actually run the script inside conda env
    print(
        Fore.CYAN
        + "🚀 Running detect_nsfw.py in Miniconda 3.12 environment..."
        + Style.RESET_ALL
    )
    subprocess.run([env_python, script_path, input_path], check=True)


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

# === Step 2: Install requirements (excluding known-incompatible NSFW libs) ===
print(Fore.CYAN + "📦 Installing dependencies..." + Style.RESET_ALL)

# Parse requirements.txt and skip tensorflow/nudenet/nsfw-detector for main env
with open(REQUIREMENTS, "r", encoding="utf-8") as rf:
    filtered = [
        line
        for line in rf
        if not any(
            skip in line.lower() for skip in ["tensorflow", "nudenet", "nsfw-detector"]
        )
    ]
with open(TEMP_REQS, "w", encoding="utf-8") as wf:
    wf.writelines(filtered)
subprocess.run([PYTHON_EXEC, "-m", "pip", "install", "-r", TEMP_REQS])
os.remove(TEMP_REQS)

# === Step 3: Define scripts in order (detect_nsfw handled separately) ===
SCRIPTS = [
    "init_tag_files.py",
    "find_duplicates.py",
    "move_duplicates.py",
    "organize_by_date.py",
    # "detect_nsfw.py",  # Run with conda, NOT in this loop
    "smart_tag_images.py",
    "smart_tag_videos.py",
    "merge_tag_logs.py",
]

# === Step 4: Determine total steps (skipping if tags exist) ===
effective_scripts = []
for script in SCRIPTS:
    if script == "init_tag_files.py":
        sfw_tags = os.path.join(CONFIG_PATH, "tags_sfw.json")
        nsfw_tags = os.path.join(CONFIG_PATH, "tags_nsfw.json")
        if os.path.isfile(sfw_tags) and os.path.isfile(nsfw_tags):
            continue
    effective_scripts.append(script)
# Add detect_nsfw.py to total steps (always runs if possible)
effective_scripts.insert(4, "detect_nsfw.py")
total_steps = len(effective_scripts)

print(Fore.MAGENTA + f"\nPipeline: {total_steps} steps to run." + Style.RESET_ALL)
pipeline_pbar = tqdm(total=total_steps, desc="📊 Pipeline Progress", colour="magenta")

# === Step 5: Run scripts, skipping as needed, handle detect_nsfw with conda ===
script_idx = 0
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
            script_idx += 1
            pipeline_pbar.update(1)
            continue

    if script == "organize_by_date.py":
        # Run NSFW detection with conda right after organizing by date
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
            pipeline_pbar.update(1)
            # Now run conda-based NSFW detection
            try:
                run_detect_nsfw_conda(input_path)
                print(
                    Fore.GREEN
                    + "✅ Completed detect_nsfw.py (Miniconda) step."
                    + Style.RESET_ALL
                )
            except Exception as e:
                print(
                    Fore.YELLOW
                    + f"⚠️ detect_nsfw.py (Miniconda) failed: {e}"
                    + Style.RESET_ALL
                )
            pipeline_pbar.update(1)
        except subprocess.CalledProcessError:
            print(
                Fore.YELLOW + f"⚠️ {script} failed. Retrying once..." + Style.RESET_ALL
            )
            try:
                result = subprocess.run(
                    [PYTHON_EXEC, script_path, input_path], check=True
                )
                duration = time.time() - start
                print(
                    Fore.GREEN
                    + f"✅ Retry succeeded for {script} in {int(duration)} seconds."
                    + Style.RESET_ALL
                )
                pipeline_pbar.update(1)
            except subprocess.CalledProcessError:
                print(
                    Fore.RED
                    + f"❌ {script} failed twice. Aborting pipeline."
                    + Style.RESET_ALL
                )
                pipeline_pbar.close()
                sys.exit(1)
        script_idx += 2
        continue

    # All other scripts run normally
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
        pipeline_pbar.update(1)
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
            pipeline_pbar.update(1)
        except subprocess.CalledProcessError:
            print(
                Fore.RED
                + f"❌ {script} failed twice. Aborting pipeline."
                + Style.RESET_ALL
            )
            pipeline_pbar.close()
            sys.exit(1)
    script_idx += 1

pipeline_pbar.close()
print(Fore.GREEN + "\n🎉 All scripts completed successfully." + Style.RESET_ALL)
