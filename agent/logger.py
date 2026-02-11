import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """
    Custom JSON log formatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if hasattr(record, "metadata"):
            log_record["metadata"] = record.metadata

        return json.dumps(log_record)


def get_logger(log_dir: Path, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    Creates and returns a configured JSON logger.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    logger = logging.getLogger("worksight-agent")
    logger.setLevel(level)

    # Prevent duplicate handlers (important!)
    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )

    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    logger.propagate = False
    return logger
