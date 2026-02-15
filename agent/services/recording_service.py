import time
import threading
from datetime import datetime
from pathlib import Path

# Ensure these imports match your actual project structure
from agent.recording.screen_recorder import record_screen
from agent.cloud.drive_client import DriveClient
from agent.config import (
    VIDEO_DIR,
    RECORDING_INTERVAL_SECONDS,
    RECORDING_DURATION_SECONDS,
)

class RecordingService:
    def __init__(self, backend, logger, hostname):  # <--- ACCEPT HOSTNAME
        self.backend = backend
        self.logger = logger
        self.hostname = hostname  # <--- STORE IT
        
        # Initialize state variables
        self.is_recording = False
        self.last_recording_time = 0

        # Initialize Drive Client with logger
        self.drive = DriveClient(logger=self.logger) 
        
        # Define folder name using the injected hostname
        # Example: "Session_DESKTOP-123_2026-02-13"
        date_str = datetime.now().strftime('%Y-%m-%d')
        self.session_folder = f"Session_{self.hostname}_{date_str}"

    def maybe_record(self):
        """Checks if it's time to record, and if so, starts a background thread."""
        now = time.time()

        if self.is_recording:
            return

        # Check if enough time has passed
        if now - self.last_recording_time < RECORDING_INTERVAL_SECONDS:
            return

        self.last_recording_time = now
        self.is_recording = True

        # Start recording in a separate thread
        thread = threading.Thread(
            target=self._record_and_upload,
            args=(now,),
            daemon=True,
        )
        thread.start()

    def _record_and_upload(self, timestamp):
        """Worker function that runs in a background thread."""
        try:
            self.logger.info(f"Starting screen recording task for {self.hostname}...")

            recording_start = datetime.utcnow()
            video_filename = f"recording_{int(timestamp)}.mp4"
            video_path = VIDEO_DIR / video_filename

            # A. Record the screen
            record_screen(
                video_path,
                duration_seconds=RECORDING_DURATION_SECONDS,
            )

            # B. Upload to Google Drive
            drive_file_id = self.drive.upload_file(
                video_path, 
                subfolder_name=self.session_folder
            )

            if not drive_file_id:
                raise Exception("Drive upload returned no File ID")

            # C. Notify Backend
            self.backend.log_recording({
                "video_path": str(video_path),
                "drive_file_id": drive_file_id,
                "started_at": recording_start.isoformat(),
                "ended_at": datetime.utcnow().isoformat(),
            })

            self.logger.info(
                f"Recording uploaded successfully to folder '{self.session_folder}'",
                extra={"metadata": {"drive_file_id": drive_file_id}},
            )

        except Exception as e:
            self.logger.error(
                "Recording cycle failed",
                extra={"metadata": {"error": str(e)}},
            )

        finally:
            self.is_recording = False
