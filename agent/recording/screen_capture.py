from datetime import datetime
from pathlib import Path
import mss
import mss.tools


def capture_screen(output_dir: Path, image_format: str = "png") -> Path:
    """
    Captures the primary screen and saves it to the given directory.
    Returns the full path of the saved screenshot.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.{image_format}"
    file_path = output_dir / filename

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(file_path))

    return file_path
