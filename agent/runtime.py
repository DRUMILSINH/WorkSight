import time
import socket  
import logging

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
        
        # 1. Identity: Capture hostname here (The Runtime owns identity)
        self.hostname = socket.gethostname()
        
        self.system_info = collect_system_info()
        self.backend = BackendClient(self.logger)

        self.screenshot_service = ScreenshotService(self.backend, self.logger)
        self.heartbeat_service = HeartbeatService(self.backend)
        
        # 2. Injection: Pass the hostname to the recording service
        self.recording_service = RecordingService(
            backend=self.backend, 
            logger=self.logger, 
            hostname=self.hostname  # <--- PASSING IT HERE
        )

    def start(self):
        self.logger.info(
            f"Agent started on {self.hostname}",
            extra={
                "metadata": {
                    "agent": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "hostname": self.hostname,
                    **self.system_info,
                }
            },
        )

        # Register the session
        session_payload = {
            "hostname": self.hostname,
            **self.system_info,
        }

        self.backend.create_session(session_payload)
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
