from pathlib import Path
from agent.recording.screen_recorder import record_screen

output = Path("agent/storage/videos/test_recording.mp4")
record_screen(output, duration_seconds=5)

print("Recording saved:", output)
