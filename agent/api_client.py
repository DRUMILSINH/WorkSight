import requests
from datetime import datetime

from agent.config import (
    SESSION_ENDPOINT,
    SCREENSHOT_ENDPOINT,
    REQUEST_TIMEOUT_SECONDS,
    AGENT_NAME,
    AGENT_VERSION
)


class BackendClient:
    def __init__(self, logger):
        self.logger = logger
        self.session_id = None

    def create_session(self, system_info: dict) -> int | None:
        try:
            payload = {
                "agent_name": AGENT_NAME,
                "agent_version": AGENT_VERSION,
                "hostname": system_info["hostname"],
                "username": system_info["username"],
                "ip_address": system_info["ip_address"],
            }

            response = requests.post(
                SESSION_ENDPOINT,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            response.raise_for_status()
            self.session_id = response.json()["session_id"]

            self.logger.info(
                "Backend session created",
                extra={"metadata": {"session_id": self.session_id}},
            )

            return self.session_id

        except Exception as e:
            self.logger.error(
                "Failed to create backend session",
                extra={"metadata": {"error": str(e)}},
            )
            return None

    def log_screenshot(self, image_path: str):
        if not self.session_id:
            return

        try:
            payload = {
                "session_id": self.session_id,
                "image_path": image_path,
                "captured_at": datetime.utcnow().isoformat() + "Z",
            }

            response = requests.post(
                SCREENSHOT_ENDPOINT,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

        except Exception as e:
            self.logger.error(
                "Failed to log screenshot",
                extra={"metadata": {"error": str(e)}},
            )
