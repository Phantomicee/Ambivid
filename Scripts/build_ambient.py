from __future__ import annotations

from pathlib import Path
import subprocess

# ======================
# CONFIG (EXACTE MAPNAMEN)
# ======================
VIDEO_DIR = Path("assets/Video_raw")
AUDIO_DIR = Path("assets/audio_raw")

OUT_SHORT = Path("Output/shorts")
OUT_LONG = Path("Output/longform")

OUT_SHORT.mkdir(parents=True, exist_ok=True)
OUT_LONG.mkdir(parents=True, exist_ok=True)

SHORT_DURATION = 10          # seconds
LONG_DURATION = 5400         # 90 minutes

# Crossfade settings (seconds)
V_CROSSFADE = 1.0
A_CROSSFADE = 1.0


def run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def newest_file(folder: Path, exts: tuple[str, ...]) -> Path:
    if not folder.exists():
        raise RuntimeError(f"Missing folder: {folder}")

    files = [
        f for f in folder.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in exts
    ]
    if not files:
        raise RuntimeError(f"No valid files found in {folder}")
    return max(files, key=lambda f: f.stat().st_mtime)


def ffprobe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd).decode("utf-8").strip()
    return float(out)


# ======================
# SHORT: 9:16 crop + merge
# ======================
def build_short_vertical(video: Path, audio: Path, out_path: Path) -> None:
    # Center crop to 9:16 based on height, then scale to 1080x1920
    # Works well when source is 16:9.
    crop_filter = (
        "crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,"
        "scale=1080:1920"
    )

    run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(audio),
        "-t", str(SHORT_DURATION),
        "-vf", crop_filter,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        out_path.as_posix(),
    ])


# ======================
# LONG: crossfade loop + merge (16:9 stays)
# ======================
def build_long_crossfade(video: Path, audio: Path, out_path: Path) -> None:
    clip_len = ffprobe_duration_seconds(video)
    if clip_len <= (V_CROSSFADE + 0.2):
        raise RuntimeError(f"Video too short for crossfade: {clip_len}s")

    # Crossfade starts near end of each loop instance
    xfade_offset = max(0.0, clip_len - V_CROSSFADE)

    # Notes:
    # - We keep video in 16:9 (no crop).
    # - We prevent "lighting drift cuts" by crossfading the last second into the next loop.
    # - Audio gets a matching acrossfade with same offset.
    filter_complex = f"""
[0:v]fps=30,format=yuv420p,split=2[v0][v1];
[v1]tpad=start_duration={xfade_offset}:start_mode=clone,trim=0:{clip_len},setpts=PTS-STARTPTS[v1s];
[v0][v1s]xfade=transition=fade:duration={V_CROSSFADE}:offset={xfade_offset},format=yuv420p[vout];

[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asplit=2[a0][a1];
[a1]adelay={int(xfade_offset*1000)}|{int(xfade_offset*1000)}[a1d];
[a0][a1d]acrossfade=d={A_CROSSFADE}:c1=tri:c2=tri[aout]
""".strip()

    run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(video),
        "-stream_loop", "-1", "-i", str(audio),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", str(LONG_DURATION),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        out_path.as_posix(),
    ])


def main() -> None:
    video = newest_file(VIDEO_DIR, (".mp4", ".mov", ".m4v", ".webm"))
    audio = newest_file(AUDIO_DIR, (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"))

    print("Using video:", video.name)
    print("Using audio:", audio.name)

    short_out = OUT_SHORT / "short_final.mp4"
    long_out = OUT_LONG / "long_ambient_90min.mp4"

    build_short_vertical(video, audio, short_out)
    build_long_crossfade(video, audio, long_out)

    print("✅ Done.")
    print("Short:", short_out)
    print("Long :", long_out)


if __name__ == "__main__":
    main()