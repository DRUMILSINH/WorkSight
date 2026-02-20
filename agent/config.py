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
AI_METRICS_ENDPOINT_TEMPLATE = f"{BACKEND_BASE_URL}/sessions/{{session_id}}/ai-metrics/"

REQUEST_TIMEOUT_SECONDS = 5
REQUEST_MAX_RETRIES = 3
REQUEST_BACKOFF_BASE_SECONDS = 1.0

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

# =========================
# Video Compression Settings
# =========================

VIDEO_COMPRESSION_ENABLED = True
VIDEO_COMPRESSION_TIMEOUT_SECONDS = 180
FFMPEG_BUNDLED_EXE = BASE_DIR / "recording" / "bin" / "ffmpeg.exe"
VIDEO_UPLOAD_TARGET_HEIGHT = 1080
VIDEO_COMPRESSION_CRF = 30
VIDEO_COMPRESSION_PRESET = "fast"

# =========================
# Heartbeat Settings
# =========================

HEARTBEAT_INTERVAL_SECONDS = 10

# =========================
# Edge AI Settings
# =========================

AI_QUEUE_DB_PATH = STORAGE_DIR / "ai_queue.sqlite3"
AI_UPLOAD_BATCH_SIZE = 20
AI_UPLOAD_POLL_SECONDS = 2
AI_MAX_RETRIES = 5
AI_BACKOFF_BASE_SECONDS = 2.0
AI_PIPELINE_TIMEOUT_SECONDS = 2.5
AI_MAX_QUEUE_BACKLOG = 1000

AI_FEATURE_VERSION = "v1"
AI_MODEL_NAME = "heuristic-edge-pipeline"
AI_MODEL_VERSION = "0.1.0"
HEALTH_SNAPSHOT_INTERVAL_SECONDS = 30
