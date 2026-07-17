from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def probe_video(path: str | Path) -> dict[str, Any]:
    video_path = Path(path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video does not exist: {video_path}")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = _run(command)
    data = json.loads(result.stdout)
    format_info = data.get("format", {})
    duration_sec = float(format_info.get("duration", 0))
    if duration_sec <= 0:
        raise ValueError(f"Video duration is not readable: {video_path}")
    video_stream = next(
        (stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"),
        {},
    )
    return {
        "path": str(video_path),
        "duration_ms": int(round(duration_sec * 1000)),
        "file_size": int(format_info.get("size") or video_path.stat().st_size),
        "format_name": format_info.get("format_name", "unknown"),
        "codec_name": video_stream.get("codec_name", "unknown"),
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "avg_frame_rate": video_stream.get("avg_frame_rate", "unknown"),
    }


def cut_clip(input_path: str | Path, output_path: str | Path, start_ms: int, end_ms: int) -> None:
    if end_ms <= start_ms:
        raise ValueError("end_ms must be greater than start_ms")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    duration_sec = (end_ms - start_ms) / 1000
    start_sec = start_ms / 1000
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-i",
        str(input_path),
        "-t",
        f"{duration_sec:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output),
    ]
    _run(command)
