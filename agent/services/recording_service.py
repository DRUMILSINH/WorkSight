import time
import threading
from datetime import datetime
from pathlib import Path

from agent.recording.screen_recorder import record_screen
from agent.cloud.drive_client import DriveClient
from agent.config import (
    VIDEO_DIR,
    RECORDING_INTERVAL_SECONDS,
    RECORDING_DURATION_SECONDS,
)


class RecordingService:
    def __init__(self, backend, logger, hostname):
        self.backend = backend
        self.logger = logger
        self.hostname = hostname

        self.is_recording = False
        self.last_recording_time = 0

        self.drive = DriveClient(logger=self.logger)

        date_str = datetime.now().strftime('%Y-%m-%d')
        self.session_folder = f"Session_{self.hostname}_{date_str}"

    def maybe_record(self):
        """Checks if recording interval has passed and starts background job."""
        now = time.time()

        if self.is_recording:
            return

        if now - self.last_recording_time < RECORDING_INTERVAL_SECONDS:
            return

        self.is_recording = True

        thread = threading.Thread(
            target=self._record_and_upload,
            args=(now,),
            daemon=True,
        )
        thread.start()

    def _record_and_upload(self, timestamp):
        video_path = None

        try:
            self.logger.info("Recording started")

            video_filename = f"recording_{int(timestamp)}.mp4"
            video_path = VIDEO_DIR / video_filename

            record_screen(
                video_path,
                duration_seconds=RECORDING_DURATION_SECONDS,
            )

            if not video_path.exists() or video_path.stat().st_size == 0:
                raise Exception("Recorded file invalid or empty")

            drive_file_id = self.drive.upload_file(
                video_path,
                subfolder_name=self.session_folder,
            )

            payload = {
                "video_path": str(video_path),
                "drive_file_id": drive_file_id,
                "started_at": datetime.utcnow().isoformat(),
                "ended_at": datetime.utcnow().isoformat(),
            }

            self.backend.log_recording(payload)

            self.logger.info(
                "Recording complete",
                extra={"metadata": {"drive_file_id": drive_file_id}},
            )

            self.last_recording_time = time.time()

        except Exception as e:
            self.logger.error(
                "Recording failed",
                extra={"metadata": {"error": str(e)}},
            )

        finally:
            self.is_recording = False
