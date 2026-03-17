from __future__ import annotations

from pathlib import Path
import subprocess


def extract_audio_ffmpeg(
    video_path: str | Path,
    audio_path: str | Path,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    source_path = Path(video_path)
    target_path = Path(audio_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        str(target_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return target_path
