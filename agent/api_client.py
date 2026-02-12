import requests
from datetime import datetime

from agent.config import (
    SESSION_ENDPOINT,
    SCREENSHOT_ENDPOINT,
    REQUEST_TIMEOUT_SECONDS,
    AGENT_NAME, 
    AGENT_VERSION,
)

class BackendClient:
    def __init__(self, logger):
        self.logger = logger
        self.session_id = None

    def create_session(self, system_info):
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
        return self.session_id

    def send_heartbeat(self):
        if not self.session_id:
            return

        requests.post(
            f"{SESSION_ENDPOINT}{self.session_id}/heartbeat/",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def log_screenshot(self, image_path):
        if not self.session_id:
            return

        payload = {
            "session_id": self.session_id,
            "image_path": str(image_path),
            "captured_at": datetime.utcnow().isoformat(),
        }

        requests.post(
            SCREENSHOT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def log_recording(self, payload):
        requests.post(
            f"{SESSION_ENDPOINT}{self.session_id}/recordings/",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
