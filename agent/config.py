import os
from pathlib import Path

# =========================
# Base Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"

SCREENSHOT_DIR = STORAGE_DIR / "screenshots"
LOG_DIR = STORAGE_DIR / "logs"

# =========================
# Screenshot Settings
# =========================

SCREENSHOT_INTERVAL_SECONDS = 10  # capture every N seconds

SCREENSHOT_FORMAT = "png"

# =========================
# Logging Settings
# =========================

LOG_FILE_NAME = "agent.log"
LOG_LEVEL = "INFO"

# =========================
# Agent Metadata
# =========================

AGENT_NAME = "WorkSight-Agent"
AGENT_VERSION = "0.1.0"
