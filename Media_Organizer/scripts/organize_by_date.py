import os
import sys
import shutil
from datetime import datetime
from PIL import Image, ExifTags
from pymediainfo import MediaInfo


def get_image_date(path):
    try:
        img = Image.open(path)
        exif = img.getexif()
        if exif:
            for tag, value in exif.items():
                name = ExifTags.TAGS.get(tag)
                if name == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def get_video_date(path):
    try:
        info = MediaInfo.parse(path)
        if info and not isinstance(info, str) and hasattr(info, 'tracks'):
            for track in info.tracks:
                if track.track_type == "General":
                    for key in ["recorded_date", "encoded_date", "tagged_date"]:
                        value = getattr(track, key, None)
                        if value:
                            try:
                                return datetime.fromisoformat(value.split("T")[0])
                            except Exception:
                                continue
    except Exception:
        pass
    return None


def get_fallback_date(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except Exception:
        return None


def get_media_date(path):
    ext = os.path.splitext(path)[1].lower()
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".heic"}
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v", ".webm"}

    if ext in image_exts:
        return get_image_date(path) or get_fallback_date(path)
    elif ext in video_exts:
        return get_video_date(path) or get_fallback_date(path)
    else:
        return get_fallback_date(path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python organize_by_date.py <input_media_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    organized_dir = os.path.join(base_path, "Organized")
    os.makedirs(organized_dir, exist_ok=True)

    print("\n📅 Organizing files by date...")
    moved = 0
    skipped = 0

    for root, _, files in os.walk(input_path):
        for filename in files:
            path = os.path.join(root, filename)
            date = get_media_date(path)

            if date:
                year, month, day = (
                    date.strftime("%Y"),
                    date.strftime("%m"),
                    date.strftime("%d"),
                )
                dest_dir = os.path.join(organized_dir, year, month, day)
                os.makedirs(dest_dir, exist_ok=True)

                dest_path = os.path.join(dest_dir, filename)
                counter = 1
                while os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    dest_path = os.path.join(dest_dir, f"{base}_dup{counter}{ext}")
                    counter += 1

                shutil.move(path, dest_path)
                print(f"✅ {filename} → {dest_path}")
                moved += 1
            else:
                print(f"⚠️ Skipped: {path}")
                skipped += 1

    print(f"\n✅ Done. Moved: {moved} files. Skipped: {skipped} files.")
    print(f"📂 Output located in: {organized_dir}")
