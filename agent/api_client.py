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
        self.token = None

    # ==============================
    # SESSION
    # ==============================

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

        data = response.json()
        self.session_id = data["session_id"]
        self.token = data["token"]

        return self.session_id

    # ==============================
    # AUTH HEADER
    # ==============================

    def _auth_headers(self):
        if not self.token:
            return {}
        return {
            "Authorization": f"Bearer {self.token}"
        }

    # ==============================
    # HEARTBEAT
    # ==============================

    def send_heartbeat(self):
        if not self.session_id:
            return

        response = requests.post(
            f"{SESSION_ENDPOINT}{self.session_id}/heartbeat/",
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

    # ==============================
    # SCREENSHOT
    # ==============================

    def log_screenshot(self, image_path):
        if not self.session_id:
            return

        payload = {
            "session_id": self.session_id,
            "image_path": str(image_path),
            "captured_at": datetime.utcnow().isoformat(),
        }

        response = requests.post(
            SCREENSHOT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

    # ==============================
    # RECORDING
    # ==============================

    def log_recording(self, payload):
        if not self.session_id:
            return

        response = requests.post(
            f"{SESSION_ENDPOINT}{self.session_id}/recordings/",
            json=payload,
            headers=self._auth_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()
