import time

from agent.api_client import BackendClient
from agent.logger import get_logger
from agent.system_info import collect_system_info
from agent.config import (
    SCREENSHOT_INTERVAL_SECONDS,
    LOG_DIR,
    LOG_FILE_NAME,
    LOG_LEVEL,
    AGENT_NAME,
    AGENT_VERSION,
)

from agent.services.screenshot_service import ScreenshotService
from agent.services.heartbeat_service import HeartbeatService
from agent.services.recording_service import RecordingService


class WorkSightAgent:
    def __init__(self):
        self.logger = get_logger(LOG_DIR, LOG_FILE_NAME, LOG_LEVEL)
        self.system_info = collect_system_info()
        self.backend = BackendClient(self.logger)

        self.screenshot_service = ScreenshotService(self.backend, self.logger)
        self.heartbeat_service = HeartbeatService(self.backend)
        self.recording_service = RecordingService(self.backend, self.logger)

    def start(self):
        self.logger.info(
            "Agent started",
            extra={
                "metadata": {
                    "agent": AGENT_NAME,
                    "version": AGENT_VERSION,
                    **self.system_info,
                }
            },
        )

        self.backend.create_session(self.system_info)

        try:
            while True:
                self.heartbeat_service.tick()
                self.screenshot_service.capture_and_send()
                self.recording_service.maybe_record()

                time.sleep(SCREENSHOT_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")

        except Exception as e:
            self.logger.error(
                "Agent crashed",
                extra={"metadata": {"error": str(e)}},
            )
