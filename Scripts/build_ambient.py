from pathlib import Path
import subprocess

# Durations
SHORT_DURATION = 10
LONG_DURATION = 5400  # 1.5 hours

# Paths
VIDEO_DIR = Path("assets/video_raw")
AUDIO_DIR = Path("assets/audio_raw")
OUT_SHORT = Path("output/shorts")
OUT_LONG = Path("output/longform")

OUT_SHORT.mkdir(parents=True, exist_ok=True)
OUT_LONG.mkdir(parents=True, exist_ok=True)

def newest_file(folder):
    files = [f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        raise RuntimeError(f"No files found in {folder}")
    return max(files, key=lambda f: f.stat().st_mtime)

video = newest_file(VIDEO_DIR)
audio = newest_file(AUDIO_DIR)

print("Using video:", video.name)
print("Using audio:", audio.name)

short_out = OUT_SHORT / "short_final.mp4"
long_out = OUT_LONG / "long_ambient_90min.mp4"

# Short
subprocess.run([
    "ffmpeg", "-y",
    "-i", str(video),
    "-i", str(audio),
    "-t", str(SHORT_DURATION),
    "-c:v", "copy",
    "-c:a", "aac",
    short_out
], check=True)

# Long
subprocess.run([
    "ffmpeg", "-y",
    "-stream_loop", "-1",
    "-i", str(video),
    "-stream_loop", "-1",
    "-i", str(audio),
    "-t", str(LONG_DURATION),
    "-c:v", "copy",
    "-c:a", "aac",
    long_out
], check=True)

print("Done. Files created:")
print(short_out)
print(long_out)
