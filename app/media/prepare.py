from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from app.intake.youtube_seed import source_id_from_url
from app.workspaces import DEFAULT_WORKSPACE, resolve_workspace

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm"}


def prepare_youtube_media(
    workspace: Path,
    youtube_url: str,
    *,
    source_id: str | None = None,
    segment_seconds: int = 300,
    format_selector: str = "bv*[height<=720]+ba/b[height<=720]/b",
    download: bool = True,
    force_download: bool = False,
    segment_mode: str = "reencode",
) -> Path:
    resolved_source_id = source_id or source_id_from_url(youtube_url)
    media_root = workspace / "datasets" / "drafts" / "media" / resolved_source_id
    media_root.mkdir(parents=True, exist_ok=True)
    source_path = media_root / "source.mp4"

    if download and (force_download or not source_path.exists()):
        download_youtube_with_ytdlp(
            youtube_url=youtube_url,
            output_path=source_path,
            format_selector=format_selector,
        )

    if not source_path.exists():
        raise FileNotFoundError(
            f"Missing source media: {source_path}. Provide it or rerun with download enabled."
        )

    segments_dir = media_root / "segments"
    segment_paths = split_media_with_ffmpeg(
        input_path=source_path,
        output_dir=segments_dir,
        source_id=resolved_source_id,
        segment_seconds=segment_seconds,
        segment_mode=segment_mode,
    )
    return write_segment_manifest(
        source_id=resolved_source_id,
        youtube_url=youtube_url,
        source_path=source_path,
        segment_paths=segment_paths,
        segment_seconds=segment_seconds,
        output_path=media_root / "segments_manifest.json",
    )


def prepare_local_media(
    workspace: Path,
    input_path: Path,
    *,
    source_id: str,
    segment_seconds: int = 300,
    segment_mode: str = "reencode",
) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(f"Missing local media file: {input_path}")
    media_root = workspace / "datasets" / "drafts" / "media" / source_id
    media_root.mkdir(parents=True, exist_ok=True)
    source_path = media_root / f"source{input_path.suffix.lower()}"
    if input_path.resolve() != source_path.resolve():
        source_path.write_bytes(input_path.read_bytes())

    segments_dir = media_root / "segments"
    segment_paths = split_media_with_ffmpeg(
        input_path=source_path,
        output_dir=segments_dir,
        source_id=source_id,
        segment_seconds=segment_seconds,
        segment_mode=segment_mode,
    )
    return write_segment_manifest(
        source_id=source_id,
        youtube_url=None,
        source_path=source_path,
        segment_paths=segment_paths,
        segment_seconds=segment_seconds,
        output_path=media_root / "segments_manifest.json",
    )


def download_youtube_with_ytdlp(
    *,
    youtube_url: str,
    output_path: Path,
    format_selector: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "yt-dlp",
        "--no-playlist",
        "--format",
        format_selector,
        "--merge-output-format",
        "mp4",
        "--output",
        str(output_path),
        youtube_url,
    ]
    subprocess.run(command, check=True)


def split_media_with_ffmpeg(
    *,
    input_path: Path,
    output_dir: Path,
    source_id: str,
    segment_seconds: int,
    segment_mode: str = "reencode",
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / f"{source_id}_part_%03d{_output_suffix(input_path)}"
    for stale_segment in output_dir.glob(f"{source_id}_part_*{_output_suffix(input_path)}"):
        stale_segment.unlink()
    command = _ffmpeg_segment_command(
        input_path=input_path,
        output_pattern=output_pattern,
        segment_seconds=segment_seconds,
        segment_mode=segment_mode,
    )
    subprocess.run(command, check=True)
    return sorted(output_dir.glob(f"{source_id}_part_*{_output_suffix(input_path)}"))


def _ffmpeg_segment_command(
    *,
    input_path: Path,
    output_pattern: Path,
    segment_seconds: int,
    segment_mode: str,
) -> list[str]:
    base = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0",
    ]
    if segment_mode == "copy":
        codec_args = ["-c", "copy"]
    elif segment_mode == "reencode":
        codec_args = [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-force_key_frames",
            f"expr:gte(t,n_forced*{segment_seconds})",
        ]
    else:
        raise ValueError("segment_mode must be 'copy' or 'reencode'")

    return [
        *base,
        *codec_args,
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        str(output_pattern),
    ]


def write_segment_manifest(
    *,
    source_id: str,
    youtube_url: str | None,
    source_path: Path,
    segment_paths: list[Path],
    segment_seconds: int,
    output_path: Path,
) -> Path:
    manifest: dict[str, Any] = {
        "source_id": source_id,
        "youtube_url": youtube_url,
        "source_media": source_path.as_posix(),
        "segment_seconds": segment_seconds,
        "segments": _manifest_segments(source_id, segment_paths, segment_seconds),
    }
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output_path


def _manifest_segments(
    source_id: str,
    segment_paths: list[Path],
    segment_seconds: int,
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    current_start = 0.0
    for index, path in enumerate(segment_paths):
        duration = probe_duration_seconds(path)
        start = current_start
        end = start + duration if duration is not None else (index + 1) * segment_seconds
        segments.append(
            {
                "index": index,
                "segment_id": f"{source_id}_part_{index:03d}",
                "media_uri": path.as_posix(),
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3) if duration is not None else None,
                "status": "needs_transcription",
            }
        )
        current_start = end
    return segments


def probe_duration_seconds(path: Path) -> float | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def _output_suffix(input_path: Path) -> str:
    suffix = input_path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return ".mp4"
    return suffix or ".mp4"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and segment media for a workspace.")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    parser.add_argument("--youtube-url")
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--source-id")
    parser.add_argument("--segment-seconds", default=300, type=int)
    parser.add_argument("--segment-mode", choices=["copy", "reencode"], default="reencode")
    parser.add_argument(
        "--format",
        default="bv*[height<=720]+ba/b[height<=720]/b",
        help="yt-dlp format selector used for YouTube downloads.",
    )
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise ValueError("workspace is required")

    if args.youtube_url:
        prepare_youtube_media(
            workspace,
            args.youtube_url,
            source_id=args.source_id,
            segment_seconds=args.segment_seconds,
            format_selector=args.format,
            download=not args.no_download,
            force_download=args.force_download,
            segment_mode=args.segment_mode,
        )
        return

    if args.input_file and args.source_id:
        prepare_local_media(
            workspace,
            args.input_file,
            source_id=args.source_id,
            segment_seconds=args.segment_seconds,
            segment_mode=args.segment_mode,
        )
        return

    raise SystemExit("Provide either --youtube-url or both --input-file and --source-id.")


if __name__ == "__main__":
    main()
