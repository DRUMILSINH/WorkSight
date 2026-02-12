import time
import threading
from datetime import datetime

from agent.recording.screen_recorder import record_screen
from agent.cloud.drive_client import DriveClient
from agent.config import (
    VIDEO_DIR,
    RECORDING_INTERVAL_SECONDS,
    RECORDING_DURATION_SECONDS,
)


class RecordingService:
    def __init__(self, backend, logger):
        self.backend = backend
        self.logger = logger
        self.drive = DriveClient()

        self.last_recording_time = 0
        self.is_recording = False

    def maybe_record(self):
        now = time.time()

        if self.is_recording:
            return

        if now - self.last_recording_time < RECORDING_INTERVAL_SECONDS:
            return

        self.last_recording_time = now
        self.is_recording = True

        thread = threading.Thread(
            target=self._record_and_upload,
            args=(now,),
            daemon=True,
        )
        thread.start()

    def _record_and_upload(self, timestamp):
        try:
            self.logger.info("Starting screen recording")

            recording_start = datetime.utcnow()
            video_path = VIDEO_DIR / f"recording_{int(timestamp)}.mp4"

            record_screen(
                video_path,
                duration_seconds=RECORDING_DURATION_SECONDS,
            )

            drive_file_id = self.drive.upload_file(video_path)

            self.backend.log_recording({
                "video_path": str(video_path),
                "drive_file_id": drive_file_id,
                "started_at": recording_start.isoformat(),
                "ended_at": datetime.utcnow().isoformat(),
            })

            self.logger.info(
                "Recording uploaded",
                extra={"metadata": {"drive_file_id": drive_file_id}},
            )

        except Exception as e:
            self.logger.error(
                "Recording failed",
                extra={"metadata": {"error": str(e)}},
            )

        finally:
            self.is_recording = False
