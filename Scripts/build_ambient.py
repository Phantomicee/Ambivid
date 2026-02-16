# Scripts/build_ambient.py
from pathlib import Path
import subprocess

# ======================
# CONFIG (EXACTE MAPNAMEN)
# ======================

VIDEO_DIR = Path("assets/Video_raw")
AUDIO_DIR = Path("assets/audio_raw")

OUT_SHORT = Path("Output/shorts")
OUT_LONG  = Path("Output/longform")

SHORT_DURATION = 10          # seconds
LONG_DURATION  = 5400        # 90 minutes

OUT_SHORT.mkdir(parents=True, exist_ok=True)
OUT_LONG.mkdir(parents=True, exist_ok=True)


def newest_file(folder: Path, exts: tuple[str, ...]) -> Path:
    files = [
        f for f in folder.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts
    ]
    if not files:
        raise RuntimeError(f"No valid files found in {folder}")
    return max(files, key=lambda f: f.stat().st_mtime)


def main():
    video = newest_file(VIDEO_DIR, (".mp4", ".mov", ".m4v", ".webm"))
    audio = newest_file(AUDIO_DIR, (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"))

    print("Using video:", video.name)
    print("Using audio:", audio.name)

    short_out = OUT_SHORT / "short_final.mp4"
    long_out  = OUT_LONG / "long_ambient_90min.mp4"

    # -------- SHORT (10s) --------
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(audio),
            "-t", str(SHORT_DURATION),
            "-c:v", "copy",
            "-c:a", "aac",
            short_out,
        ],
        check=True,
    )

    # -------- LONG FORM (90 min, loop) --------
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(video),
            "-stream_loop", "-1", "-i", str(audio),
            "-t", str(LONG_DURATION),
            "-c:v", "copy",
            "-c:a", "aac",
            long_out,
        ],
        check=True,
    )

    print("✅ Build complete")
    print("Short:", short_out)
    print("Long :", long_out)


if __name__ == "__main__":
    main()