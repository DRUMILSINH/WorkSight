import sys
import threading
import types

from agent.services.recording_service import RecordingService


class _Logger:
    def __init__(self):
        self.errors = []
        self.infos = []

    def info(self, message, extra=None):
        self.infos.append((message, extra))

    def warning(self, *args, **kwargs):
        pass

    def error(self, message, extra=None):
        self.errors.append((message, extra))


class _Backend:
    def __init__(self, fail=False):
        self.payloads = []
        self.fail = fail

    def log_recording(self, payload):
        self.payloads.append(payload)
        if self.fail:
            raise RuntimeError("backend down")


class _Drive:
    def __init__(self, file_id="drive-123"):
        self.file_id = file_id
        self.calls = []

    def upload_file(self, path, subfolder_name=None):
        self.calls.append((path, subfolder_name))
        return self.file_id


def _inject_fake_screen_recorder(monkeypatch):
    fake_module = types.ModuleType("agent.recording.screen_recorder")

    def record_screen(path, duration_seconds):
        path.write_bytes(b"video-bytes")

    fake_module.record_screen = record_screen
    monkeypatch.setitem(sys.modules, "agent.recording.screen_recorder", fake_module)


def test_recording_successful_flow_logs_uploaded(monkeypatch):
    _inject_fake_screen_recorder(monkeypatch)
    monkeypatch.setattr("agent.services.recording_service.compress_video", lambda p, logger=None: p)

    backend = _Backend()
    logger = _Logger()
    drive = _Drive(file_id="file-1")
    service = RecordingService(backend=backend, logger=logger, hostname="host1", drive_client=drive)

    service._record_and_upload(1700000000)

    assert service.is_recording is False
    assert len(backend.payloads) == 1
    assert backend.payloads[0]["status"] == "UPLOADED"
    assert backend.payloads[0]["drive_file_id"] == "file-1"


def test_recording_drive_failure_logs_failed_payload(monkeypatch):
    _inject_fake_screen_recorder(monkeypatch)
    monkeypatch.setattr("agent.services.recording_service.compress_video", lambda p, logger=None: p)

    backend = _Backend()
    logger = _Logger()
    drive = _Drive(file_id=None)
    service = RecordingService(backend=backend, logger=logger, hostname="host1", drive_client=drive)

    service._record_and_upload(1700000001)

    assert service.is_recording is False
    assert len(backend.payloads) == 1
    assert backend.payloads[0]["status"] == "FAILED"
    assert backend.payloads[0]["drive_file_id"] is None


def test_recording_compression_fallback_still_uploads(monkeypatch):
    _inject_fake_screen_recorder(monkeypatch)
    monkeypatch.setattr("agent.services.recording_service.compress_video", lambda p, logger=None: p)

    backend = _Backend()
    logger = _Logger()
    drive = _Drive(file_id="file-4")
    service = RecordingService(backend=backend, logger=logger, hostname="host1", drive_client=drive)

    service._record_and_upload(1700000003)

    assert len(drive.calls) == 1
    assert backend.payloads[0]["status"] == "UPLOADED"


def test_recording_backend_failure_does_not_leave_stuck_state(monkeypatch):
    _inject_fake_screen_recorder(monkeypatch)
    monkeypatch.setattr("agent.services.recording_service.compress_video", lambda p, logger=None: p)

    backend = _Backend(fail=True)
    logger = _Logger()
    drive = _Drive(file_id="file-2")
    service = RecordingService(backend=backend, logger=logger, hostname="host1", drive_client=drive)

    service.is_recording = True
    service._record_and_upload(1700000002)

    assert service.is_recording is False
    assert any("Recording backend logging failed" in msg for msg, _ in logger.errors)


def test_maybe_record_respects_stop_event():
    backend = _Backend()
    logger = _Logger()
    drive = _Drive(file_id="file-3")
    stop_event = threading.Event()
    stop_event.set()
    service = RecordingService(
        backend=backend,
        logger=logger,
        hostname="host1",
        stop_event=stop_event,
        drive_client=drive,
    )

    service.maybe_record()

    assert service.is_recording is False
