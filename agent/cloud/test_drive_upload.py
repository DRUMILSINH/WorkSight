from pathlib import Path
from agent.cloud.drive_client import DriveClient

BASE_DIR = Path(__file__).resolve().parents[2]
video_path = BASE_DIR / "agent" / "storage" / "videos" / "test_recording.mp4"

client = DriveClient()
file_id = client.upload_file(video_path)

print("Uploaded to Drive, file ID:", file_id)
