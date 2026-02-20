__all__ = [
    "ScreenshotService",
    "HeartbeatService",
    "RecordingService",
    "AIService",
]


def __getattr__(name):
    if name == "ScreenshotService":
        from .screenshot_service import ScreenshotService
        return ScreenshotService
    if name == "HeartbeatService":
        from .heartbeat_service import HeartbeatService
        return HeartbeatService
    if name == "RecordingService":
        from .recording_service import RecordingService
        return RecordingService
    if name == "AIService":
        from .ai_service import AIService
        return AIService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
