from datetime import datetime
from agent.recording.screen_capture import capture_screen
from agent.storage.local import LocalStorage
from agent.storage.cleanup import cleanup_old_screenshots
from agent.config import SCREENSHOT_DIR


class ScreenshotService:
    def __init__(self, backend, logger):
        self.backend = backend
        self.logger = logger
        self.storage = LocalStorage()

    def capture_and_send(self):
        screenshot_path = capture_screen(SCREENSHOT_DIR)
        stored_path = self.storage.save(screenshot_path)

        self.backend.log_screenshot(stored_path)

        cleanup_old_screenshots(SCREENSHOT_DIR)

        self.logger.info(
            "Screenshot captured",
            extra={"metadata": {"path": str(screenshot_path)}},
        )
