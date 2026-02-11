import time
from pathlib import Path



from agent.config import (
    SCREENSHOT_DIR,
    SCREENSHOT_INTERVAL_SECONDS,
    LOG_DIR,
    LOG_FILE_NAME,
    LOG_LEVEL,
    AGENT_NAME,
    AGENT_VERSION,
)
from agent.system_info import collect_system_info
from agent.screen_capture import capture_screen
from agent.logger import get_logger


class WorkSightAgent:
    def __init__(self):
        self.logger = get_logger(LOG_DIR, LOG_FILE_NAME, LOG_LEVEL)
        self.system_info = collect_system_info()

    def start(self):
        self.logger.info(
            "Agent started",
            extra={
                "metadata": {
                    "agent": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "system": self.system_info,
                }
            },
        )

        try:
            while True:
                screenshot_path = capture_screen(SCREENSHOT_DIR)

                self.logger.info(
                    "Screenshot captured",
                    extra={
                        "metadata": {
                            "path": str(screenshot_path),
                        }
                    },
                )

                time.sleep(SCREENSHOT_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")
        except Exception as e:
            self.logger.error(
                "Agent crashed",
                extra={"metadata": {"error": str(e)}},
            )
