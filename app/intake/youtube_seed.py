from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

from app.workspaces import DEFAULT_WORKSPACE, resolve_workspace


def video_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/")
    else:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
    if not video_id:
        raise ValueError(f"Could not extract YouTube video ID from URL: {url}")
    return video_id


def source_id_from_url(url: str) -> str:
    return f"youtube_{video_id_from_url(url)}"


def fetch_youtube_oembed(url: str, timeout_seconds: float = 10.0) -> dict[str, str]:
    endpoint = "https://www.youtube.com/oembed"
    query = urlencode({"url": url, "format": "json"})
    request_url = f"{endpoint}?{query}"
    try:
        with urlopen(request_url, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return {}

    return {
        "title": str(payload.get("title", "")),
        "channel": str(payload.get("author_name", "")),
    }


def seed_youtube_source(
    workspace: Path,
    youtube_url: str,
    *,
    title: str | None = None,
    channel: str | None = None,
    expected_speakers: list[str] | None = None,
    clip_start: float = 0.0,
    clip_end: float | None = None,
    fetch_metadata: bool = True,
) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    source_id = source_id_from_url(youtube_url)
    metadata = fetch_youtube_oembed(youtube_url) if fetch_metadata else {}
    resolved_title = title if title is not None else metadata.get("title", "")
    resolved_channel = channel if channel is not None else metadata.get("channel", "")
    speakers = expected_speakers or []

    _append_intake_row(
        workspace / "intake" / "youtube_links.jsonl",
        {
            "source_id": source_id,
            "youtube_url": youtube_url,
            "title": resolved_title,
            "channel": resolved_channel,
            "expected_speakers": speakers,
            "useful_ranges": _useful_ranges(clip_start, clip_end),
            "status": "draft_created",
            "notes": "Seeded from YouTube URL. Needs transcript, diarization, and reviewed labels.",
        },
    )

    draft_case = _build_draft_case(
        source_id=source_id,
        youtube_url=youtube_url,
        title=resolved_title,
        channel=resolved_channel,
        expected_speakers=speakers,
        clip_start=clip_start,
        clip_end=clip_end,
    )
    draft_path = workspace / "datasets" / "drafts" / "cases" / f"{source_id}.json"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(draft_case, indent=2) + "\n", encoding="utf-8")
    _ensure_manifest_case(workspace / "datasets" / "drafts" / "manifest.json", draft_path.name)
    return draft_path


def _append_intake_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing_rows.append(json.loads(line))

    replaced = False
    updated_rows: list[dict[str, Any]] = []
    for existing in existing_rows:
        if existing.get("source_id") == row["source_id"]:
            updated_rows.append(row)
            replaced = True
        else:
            updated_rows.append(existing)
    if not replaced:
        updated_rows.append(row)

    path.write_text(
        "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in updated_rows),
        encoding="utf-8",
    )


def _ensure_manifest_case(path: Path, case_filename: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "name": "drafts",
            "description": "Partially prepared cases that are not yet gold-labelled.",
            "cases": [],
        }
    cases = manifest.setdefault("cases", [])
    if case_filename not in cases:
        cases.append(case_filename)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _useful_ranges(clip_start: float, clip_end: float | None) -> list[dict[str, Any]]:
    if clip_end is None:
        return []
    return [{"start": clip_start, "end": clip_end, "reason": "initial selected range"}]


def _build_draft_case(
    *,
    source_id: str,
    youtube_url: str,
    title: str,
    channel: str,
    expected_speakers: list[str],
    clip_start: float,
    clip_end: float | None,
) -> dict[str, Any]:
    speakers = [
        {
            "person_id": index,
            "display_name": name,
            "speaker_type": "known",
            "aliases": [],
            "role": "",
            "notes": "Expected speaker from intake.",
        }
        for index, name in enumerate(expected_speakers, start=1)
    ]
    return {
        "case_id": source_id,
        "source": {
            "input_type": "youtube_url",
            "youtube_url": youtube_url,
            "source_id": source_id,
            "title": title,
            "channel": channel,
            "notes": "Seeded from YouTube URL.",
        },
        "media": {
            "media_type": "video",
            "media_uri": f"media/{source_id}.mp4",
            "clip_start": clip_start,
            "clip_end": clip_end,
        },
        "media_uri": f"media/{source_id}.mp4",
        "known_people_set_id": "seed_podcast",
        "media_type": "video",
        "conditions": {
            "speaker_count": len(expected_speakers),
            "has_unknown_speakers": True,
            "overlap_level": "unknown",
            "face_visibility": "unknown",
            "audio_quality": "unknown",
        },
        "speakers": speakers,
        "segments": [],
        "annotation": {
            "status": "draft",
            "reviewed_by": "",
            "review_level": "rough",
            "notes": "Needs transcript, diarization, and reviewed speaker labels.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a workspace draft case from a YouTube URL.")
    parser.add_argument("youtube_url")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    parser.add_argument("--title")
    parser.add_argument("--channel")
    parser.add_argument("--expected-speaker", action="append", default=[])
    parser.add_argument("--clip-start", default=0.0, type=float)
    parser.add_argument("--clip-end", type=float)
    parser.add_argument("--no-fetch-metadata", action="store_true")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise ValueError("workspace is required")
    seed_youtube_source(
        workspace,
        args.youtube_url,
        title=args.title,
        channel=args.channel,
        expected_speakers=args.expected_speaker,
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        fetch_metadata=not args.no_fetch_metadata,
    )


if __name__ == "__main__":
    main()
