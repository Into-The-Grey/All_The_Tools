import os
import sys
import shutil
import csv

try:
    from nudenet import NudeClassifier
except ImportError:
    print(
        "❌ NudeNet not installed or import failed. Please check your venv and pip install nudenet."
    )
    sys.exit(1)


def classify_and_tag(input_media_dir, base_dir):
    print("🔎 Initializing NSFW classifier (this may take a sec)...")
    classifier = NudeClassifier()

    tagged_dir = os.path.join(base_dir, "Tagged", "NSFW")
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(tagged_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(logs_dir, "nsfw_log.csv")
    files_classified = 0

    with open(log_path, "w", newline="", encoding="utf-8") as logfile:
        writer = csv.writer(logfile)
        writer.writerow(["File", "Classification", "UnsafeScore", "NewLocation"])

        for root, _, files in os.walk(os.path.join(base_dir, "Organized")):
            for file in files:
                path = os.path.join(root, file)
                if not os.path.isfile(path):
                    continue

                result = classifier.classify(path)
                scores = result.get(path)
                if not scores:
                    continue

                unsafe_score = scores.get("unsafe", 0)
                classification = "unsafe" if unsafe_score > 0.8 else "safe"

                if classification == "unsafe":
                    dest_path = os.path.join(tagged_dir, file)
                    counter = 1
                    while os.path.exists(dest_path):
                        base, ext = os.path.splitext(file)
                        dest_path = os.path.join(
                            tagged_dir, f"{base}_dup{counter}{ext}"
                        )
                        counter += 1
                    shutil.move(path, dest_path)
                    print(f"🚫 Moved NSFW file: {file} → {dest_path}")
                    writer.writerow([path, classification, unsafe_score, dest_path])
                else:
                    writer.writerow([path, classification, unsafe_score, ""])

                files_classified += 1

    print(f"\n✅ Done. Classified {files_classified} files.")
    print(f"📄 NSFW log saved to: {log_path}")
    print(f"📁 NSFW files moved to: {tagged_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_nsfw.py <input_media_directory>")
        sys.exit(1)

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_media_dir = sys.argv[1]

    classify_and_tag(input_media_dir, base_path)
