import cv2
import time
import numpy as np
from pathlib import Path
from mss import mss


def record_screen(output_path: Path, duration_seconds: int = 10, fps: int = 10):
    """
    Records screen for given duration and saves as MP4.
    """
    with mss() as sct:
        monitor = sct.monitors[1]  # primary screen
        width = monitor["width"]
        height = monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (width, height),
        )

        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            video.write(frame)

        video.release()
