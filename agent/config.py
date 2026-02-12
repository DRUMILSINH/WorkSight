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

# =========================
# Backend API Settings
# =========================

BACKEND_BASE_URL = "http://127.0.0.1:8080/api"

SESSION_ENDPOINT = f"{BACKEND_BASE_URL}/sessions/"
SCREENSHOT_ENDPOINT = f"{BACKEND_BASE_URL}/screenshots/"

REQUEST_TIMEOUT_SECONDS = 5

# =========================
# Storage Policy
# =========================

MAX_SCREENSHOTS = 100        # keep last N screenshots
SCREENSHOT_RETENTION_DAYS = 1  # optional (future)

# =========================
# Recording Settings
# =========================

RECORDING_INTERVAL_SECONDS = 20      # record every 60 seconds
RECORDING_DURATION_SECONDS = 10      # 10 second video clip

VIDEO_DIR = STORAGE_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
