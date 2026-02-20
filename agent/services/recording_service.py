import time
import threading
from datetime import datetime, timezone

from agent.config import (
    VIDEO_DIR,
    RECORDING_INTERVAL_SECONDS,
    RECORDING_DURATION_SECONDS,
    VIDEO_COMPRESSION_ENABLED,
)
from agent.recording.video_compressor import compress_video


class RecordingService:
    def __init__(self, backend, logger, hostname, stop_event=None, drive_client=None):
        self.backend = backend
        self.logger = logger
        self.hostname = hostname
        self.stop_event = stop_event

        self.is_recording = False
        self.last_recording_time = 0

        self.drive = drive_client
        if self.drive is None:
            try:
                from agent.cloud.drive_client import DriveClient
                self.drive = DriveClient(logger=self.logger)
            except Exception as exc:
                self.logger.error(
                    "Drive client initialization failed",
                    extra={"metadata": {"error": str(exc)}},
                )
                self.drive = None

        date_str = datetime.now().strftime('%Y-%m-%d')
        self.session_folder = f"Session_{self.hostname}_{date_str}"

    def maybe_record(self):
        """Checks if recording interval has passed and starts background job."""
        if self._should_stop():
            return

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
        stage = "record_started"
        started_at = datetime.now(timezone.utc).isoformat()
        ended_at = started_at

        try:
            if self._should_stop():
                self.logger.info("Recording skipped due to stop signal")
                return

            self.logger.info(
                "Recording stage",
                extra={"metadata": {"stage": stage}},
            )

            video_filename = f"recording_{int(timestamp)}.mp4"
            video_path = VIDEO_DIR / video_filename

            from agent.recording.screen_recorder import record_screen
            record_screen(
                video_path,
                duration_seconds=RECORDING_DURATION_SECONDS,
            )

            ended_at = datetime.now(timezone.utc).isoformat()

            if not video_path.exists() or video_path.stat().st_size == 0:
                raise RuntimeError("Recorded file invalid or empty")

            stage = "recorded"
            self.logger.info(
                "Recording stage",
                extra={"metadata": {"stage": stage, "path": str(video_path)}},
            )

            if VIDEO_COMPRESSION_ENABLED:
                video_path = compress_video(video_path, logger=self.logger)
                stage = "compressed"
            else:
                stage = "compression_skipped"

            self.logger.info(
                "Recording stage",
                extra={"metadata": {"stage": stage, "path": str(video_path)}},
            )

            if self._should_stop():
                self.logger.info("Recording upload skipped due to stop signal")
                return

            stage = "upload_attempted"
            drive_file_id = self.drive.upload_file(
                video_path,
                subfolder_name=self.session_folder,
            ) if self.drive else None

            if not drive_file_id:
                raise RuntimeError("Drive upload failed or returned no file id")

            stage = "uploaded"
            self.logger.info(
                "Recording stage",
                extra={
                    "metadata": {
                        "stage": stage,
                        "drive_file_id": drive_file_id,
                        "path": str(video_path),
                    }
                },
            )

            payload = {
                "video_path": str(video_path),
                "drive_file_id": drive_file_id,
                "started_at": started_at,
                "ended_at": ended_at,
                "file_size_bytes": video_path.stat().st_size,
                "status": "UPLOADED",
            }

            self.backend.log_recording(payload)
            stage = "backend_logged"

            self.logger.info(
                "Recording complete",
                extra={
                    "metadata": {
                        "stage": stage,
                        "drive_file_id": drive_file_id,
                        "path": str(video_path),
                    }
                },
            )
            self.logger.info(
                "Recording retention policy: local files are kept after upload",
                extra={"metadata": {"path": str(video_path)}},
            )

            self.last_recording_time = time.time()

        except Exception as e:
            failed_payload = None
            if video_path is not None:
                file_size = None
                try:
                    if video_path.exists():
                        file_size = video_path.stat().st_size
                except Exception:
                    file_size = None

                failed_payload = {
                    "video_path": str(video_path),
                    "drive_file_id": None,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "file_size_bytes": file_size,
                    "status": "FAILED",
                }

            if failed_payload is not None:
                try:
                    self.backend.log_recording(failed_payload)
                except Exception as backend_exc:
                    self.logger.error(
                        "Recording backend logging failed",
                        extra={
                            "metadata": {
                                "stage": stage,
                                "error": str(backend_exc),
                                "path": str(video_path) if video_path else None,
                            }
                        },
                    )

            self.logger.error(
                "Recording failed",
                extra={
                    "metadata": {
                        "stage": stage,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "path": str(video_path) if video_path else None,
                    }
                },
            )

        finally:
            self.is_recording = False

    def _should_stop(self) -> bool:
        return self.stop_event.is_set() if self.stop_event else False
