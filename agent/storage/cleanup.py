from pathlib import Path
from agent.config import MAX_SCREENSHOTS


def cleanup_old_screenshots(directory: Path):
    screenshots = sorted(
        directory.glob("*.png"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    for old_file in screenshots[MAX_SCREENSHOTS:]:
        try:
            old_file.unlink()
        except Exception:
            pass
