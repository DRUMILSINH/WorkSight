import requests
import time
from datetime import datetime, timezone

from agent.config import (
    SESSION_ENDPOINT,
    SCREENSHOT_ENDPOINT,
    AI_METRICS_ENDPOINT_TEMPLATE,
    REQUEST_TIMEOUT_SECONDS,
    REQUEST_MAX_RETRIES,
    REQUEST_BACKOFF_BASE_SECONDS,
    AGENT_NAME,
    AGENT_VERSION,
)


class BackendClient:
    def __init__(self, logger):
        self.logger = logger
        self.session_id = None
        self.token = None
        self.last_ai_upload_success_at = None

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

        response = self._post_with_retry(
            SESSION_ENDPOINT,
            json=payload,
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

        response = self._post_with_retry(
            f"{SESSION_ENDPOINT}{self.session_id}/heartbeat/",
            headers=self._auth_headers(),
        )
        response.raise_for_status()

    # ==============================
    # SCREENSHOT
    # ==============================

    def log_screenshot(self, image_path):
        if not self.session_id:
            return

        with open(image_path, "rb") as img_file:
            files = {
                "image": img_file
            }

            data = {
                "session_id": self.session_id,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }

            response = self._post_with_retry(
                SCREENSHOT_ENDPOINT,
                files=files,
                data=data,
                headers=self._auth_headers(),
            )

            response.raise_for_status()


    # ==============================
    # RECORDING
    # ==============================

    def log_recording(self, payload):
        if not self.session_id:
            return

        response = self._post_with_retry(
            f"{SESSION_ENDPOINT}{self.session_id}/recordings/",
            json=payload,
            headers=self._auth_headers(),
        )

        response.raise_for_status()

    # ==============================
    # AI METRICS
    # ==============================

    def log_ai_metric(self, payload, idempotency_key):
        if not self.session_id:
            return

        headers = self._auth_headers()
        headers["X-Idempotency-Key"] = idempotency_key

        response = self._post_with_retry(
            AI_METRICS_ENDPOINT_TEMPLATE.format(session_id=self.session_id),
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        self.last_ai_upload_success_at = datetime.now(timezone.utc).isoformat()
        return response.json()

    def _post_with_retry(self, url, **kwargs):
        attempts = 0
        last_error = None

        while attempts < REQUEST_MAX_RETRIES:
            attempts += 1
            try:
                response = requests.post(
                    url,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    **kwargs,
                )
                if response.status_code >= 500:
                    raise requests.HTTPError(f"Server error {response.status_code}")
                return response
            except (requests.RequestException, requests.HTTPError) as exc:
                last_error = exc
                if attempts >= REQUEST_MAX_RETRIES:
                    break
                backoff = REQUEST_BACKOFF_BASE_SECONDS * (2 ** (attempts - 1))
                time.sleep(backoff)

        raise last_error
