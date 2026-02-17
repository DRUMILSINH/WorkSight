"""
Google Drive Authentication Setup
---------------------------------
Run once to generate token.json for the agent.
This version uses absolute paths and proper logging.
"""

import logging
import sys
from pathlib import Path

from pydrive2.auth import GoogleAuth


# =========================
# Absolute Path Resolution
# =========================

# agent/cloud/setup_drive_auth.py
CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parent.parent        # agent/
PROJECT_ROOT = BASE_DIR.parent               # WorkSight/

CREDENTIALS_DIR = BASE_DIR / "credentials"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

LOG_DIR = BASE_DIR / "storage" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "setup_auth.log"


# =========================
# Logging Setup
# =========================

def setup_logger():
    logger = logging.getLogger("setup_drive_auth")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# =========================
# Main Setup Logic
# =========================

def main():
    logger = setup_logger()

    logger.info("=" * 60)
    logger.info("Starting Google Drive authentication setup...")

    # 1️⃣ Validate credentials.json exists
    if not CLIENT_SECRET_FILE.exists():
        logger.error(f"❌ credentials.json not found at: {CLIENT_SECRET_FILE}")
        sys.exit(1)

    logger.info("✓ credentials.json found")

    try:
        gauth = GoogleAuth()

        # Force offline access (refresh token support)
        gauth.settings["client_config_file"] = str(CLIENT_SECRET_FILE)
        gauth.settings["get_refresh_token"] = True

        logger.info("Opening browser for authentication...")
        gauth.LocalWebserverAuth()

        # Save token
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        gauth.SaveCredentialsFile(str(TOKEN_FILE))

        # Verify file created
        if not TOKEN_FILE.exists():
            logger.error("❌ token.json was not created.")
            sys.exit(1)

        size = TOKEN_FILE.stat().st_size
        if size < 500:
            logger.error("❌ token.json created but appears invalid (too small).")
            sys.exit(1)

        logger.info(f"✓ token.json created successfully at: {TOKEN_FILE}")
        logger.info(f"File size: {size} bytes")
        logger.info("✅ Authentication complete!")

    except Exception as e:
        logger.exception("❌ Authentication failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
