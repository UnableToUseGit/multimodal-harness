"""Frame sampling helpers for multimodal generation."""

from __future__ import annotations

import base64
import queue
import threading
import time

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None
    print("OpenCV not found!")


def get_frame_indices(video_path, start=0, end=None, n_frames=None, fps=None, max_frames=None):
    if (n_frames is None and fps is None) or (n_frames is not None and fps is not None):
        raise ValueError("Either n_frames or fps must be provided, but not both.")

    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    start_frame = int(start * video_fps)
    end_frame = int(end * video_fps) if end is not None else total_frames - 1
    end_frame = min(end_frame, total_frames - 1)

    if start_frame >= end_frame:
        return np.array([], dtype=int)

    if n_frames is not None:
        indices = np.linspace(start_frame, end_frame, n_frames).astype(int)
    else:
        step = video_fps / fps
        indices = np.arange(start_frame, end_frame, step).astype(int)

    if max_frames is not None and len(indices) > max_frames:
        indices = np.linspace(start_frame, end_frame, max_frames).astype(int)

    return indices


def process_one_frame(frame, max_resolution):
    if frame is None:
        return None

    original_height, original_width = frame.shape[:2]

    if max_resolution is not None and (original_width > max_resolution or original_height > max_resolution):
        n_width = int(max_resolution * original_width / max(original_width, original_height))
        n_height = int(max_resolution * original_height / max(original_width, original_height))
    else:
        n_width = original_width
        n_height = original_height

    resized = cv2.resize(frame, (n_width, n_height))
    _, buffer = cv2.imencode(".jpg", resized)
    return base64.b64encode(buffer).decode("utf-8")


def prepare_video_input(video_path, indices, max_resolution, max_workers=4):
    frame_queue = queue.Queue(maxsize=max_workers * 2)
    result_queue = queue.Queue()

    def producer():
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.set(cv2.CAP_PROP_POS_FRAMES, indices[0])
        current_pos = indices[0]

        for idx in indices:
            if idx < current_pos:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                current_pos = idx

            while current_pos < idx:
                cap.grab()
                current_pos += 1

            ret, frame = cap.read()
            if ret:
                timestamp = idx / fps if fps > 0 else 0
                frame_queue.put((idx, frame, timestamp))
            current_pos += 1

        cap.release()
        for _ in range(max_workers):
            frame_queue.put(None)

    def worker():
        while True:
            item = frame_queue.get()
            if item is None:
                frame_queue.task_done()
                break

            idx, frame, timestamp = item
            result_queue.put((idx, process_one_frame(frame, max_resolution), timestamp))
            frame_queue.task_done()

    producer_thread = threading.Thread(target=producer)
    producer_thread.start()

    workers = []
    for _ in range(max_workers):
        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        workers.append(worker_thread)

    producer_thread.join()
    frame_queue.join()

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    results.sort(key=lambda item: item[0])
    frames = [item[1] for item in results]
    timestamps = [item[2] for item in results]
    return frames, timestamps
