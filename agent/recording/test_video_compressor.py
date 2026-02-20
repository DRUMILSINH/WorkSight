from pathlib import Path
import subprocess

from agent.recording.video_compressor import compress_video


class _Logger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


def test_compress_video_replaces_original_on_success(tmp_path, monkeypatch):
    input_path = tmp_path / "clip.mp4"
    input_path.write_bytes(b"original")

    def fake_run(cmd, check, timeout, capture_output, text):
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"compressed")
        return 0

    monkeypatch.setattr("agent.recording.video_compressor.subprocess.run", fake_run)

    result = compress_video(input_path, logger=_Logger())

    assert result == input_path
    assert input_path.exists()
    assert input_path.read_bytes() == b"compressed"


def test_compress_video_falls_back_to_original_on_failure(tmp_path, monkeypatch):
    input_path = tmp_path / "clip.mp4"
    input_path.write_bytes(b"original")

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd="ffmpeg")

    monkeypatch.setattr("agent.recording.video_compressor.subprocess.run", fake_run)

    result = compress_video(input_path, logger=_Logger())

    assert result == input_path
    assert input_path.exists()
    assert input_path.read_bytes() == b"original"
