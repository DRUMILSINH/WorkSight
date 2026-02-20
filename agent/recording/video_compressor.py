import subprocess
from pathlib import Path

from agent.config import (
    FFMPEG_BUNDLED_EXE,
    VIDEO_COMPRESSION_CRF,
    VIDEO_COMPRESSION_PRESET,
    VIDEO_COMPRESSION_TIMEOUT_SECONDS,
    VIDEO_UPLOAD_TARGET_HEIGHT,
)


def _resolve_ffmpeg_executable() -> str:
    if FFMPEG_BUNDLED_EXE.exists():
        return str(FFMPEG_BUNDLED_EXE)
    return "ffmpeg"


def compress_video(input_path: Path, logger=None) -> Path:
    if not input_path.exists() or input_path.stat().st_size == 0:
        if logger:
            logger.warning(
                "Compression skipped for missing or empty file",
                extra={"metadata": {"path": str(input_path)}},
            )
        return input_path

    compressed_path = input_path.with_name(f"{input_path.stem}_compressed{input_path.suffix}")
    ffmpeg_exe = _resolve_ffmpeg_executable()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(input_path),
        "-vf",
        f"scale={VIDEO_UPLOAD_TARGET_HEIGHT}:-2",
        "-c:v",
        "libx264",
        "-preset",
        VIDEO_COMPRESSION_PRESET,
        "-crf",
        str(VIDEO_COMPRESSION_CRF),
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "faststart",
        str(compressed_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            timeout=VIDEO_COMPRESSION_TIMEOUT_SECONDS,
            capture_output=True,
            text=True,
        )

        if not compressed_path.exists() or compressed_path.stat().st_size == 0:
            raise RuntimeError("Compressed output missing or empty")

        compressed_path.replace(input_path)
        if logger:
            logger.info(
                "Video compression completed",
                extra={
                    "metadata": {
                        "path": str(input_path),
                        "ffmpeg": ffmpeg_exe,
                    }
                },
            )
        return input_path

    except Exception as exc:
        if compressed_path.exists():
            try:
                compressed_path.unlink()
            except Exception:
                pass

        if logger:
            logger.warning(
                "Video compression failed; using original file",
                extra={
                    "metadata": {
                        "path": str(input_path),
                        "ffmpeg": ffmpeg_exe,
                        "error": str(exc),
                    }
                },
            )
        return input_path
