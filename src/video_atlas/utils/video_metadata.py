"""Video metadata helpers."""

from __future__ import annotations

import json
import os
from typing import Dict

try:
    import cv2
except ImportError:
    cv2 = None
    print("OpenCV not found!")


def get_video_property(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution = f"{width}x{height}"
        cap.release()
    except Exception:
        fps = None
        duration = None
        resolution = None

    return {
        "video_path": video_path,
        "duration": duration,
        "fps": fps,
        "resolution": resolution,
    }


def read_json(json_path: str) -> Dict:
    if not os.path.exists(json_path):
        return {}
    with open(json_path, "r", encoding="utf-8", errors="replace") as file:
        return json.load(file)
