from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
DEFAULT_MODEL = "gpt-4o-transcribe-diarize"
PROVIDER_NAME = "openai_diarized_transcription"


def populate_draft_cases(
    *,
    workspace: Path,
    case_glob: str,
    model: str = DEFAULT_MODEL,
    force: bool = False,
) -> list[Path]:
    cases_dir = workspace / "datasets" / "drafts" / "cases"
    case_paths = sorted(cases_dir.glob(case_glob))
    if not case_paths:
        raise FileNotFoundError(f"No draft cases matched {cases_dir / case_glob}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI diarized transcription.")

    updated_paths: list[Path] = []
    for case_path in case_paths:
        case = _read_json(case_path)
        media_path = _case_media_path(workspace, case)
        audio_path = _audio_cache_path(workspace, case, media_path)
        raw_path = _provider_output_path(workspace, case)

        ensure_audio_for_transcription(media_path=media_path, audio_path=audio_path)
        response: Mapping[str, Any]
        if force or not raw_path.exists():
            response = transcribe_with_openai(
                api_key=api_key,
                audio_path=audio_path,
                model=model,
            )
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            _write_json(
                raw_path,
                {
                    "provider": PROVIDER_NAME,
                    "model": model,
                    "case_id": case["case_id"],
                    "media_uri": case.get("media_uri"),
                    "audio_cache_uri": _relative_to_workspace(workspace, audio_path),
                    "response": response,
                },
            )
        else:
            cached = _read_json(raw_path)
            response = _response_payload(cached)

        updated_case = draft_case_from_diarized_response(
            case=case,
            response=response,
            provider_output_path=raw_path,
            workspace=workspace,
            model=model,
        )
        _write_json(case_path, updated_case)
        updated_paths.append(case_path)

    return updated_paths


def ensure_audio_for_transcription(*, media_path: Path, audio_path: Path) -> None:
    if audio_path.exists() and audio_path.stat().st_size > 0:
        return
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(media_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "64k",
        str(audio_path),
    ]
    subprocess.run(command, check=True, capture_output=True)


def transcribe_with_openai(*, api_key: str, audio_path: Path, model: str) -> dict[str, Any]:
    fields = {
        "model": model,
        "response_format": "diarized_json",
        "chunking_strategy": "auto",
        "language": "en",
    }
    body, content_type = _multipart_form_data(fields=fields, file_path=audio_path)
    request = urllib.request.Request(
        OPENAI_TRANSCRIPTIONS_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        message = f"OpenAI transcription failed with HTTP {error.code}: {details}"
        raise RuntimeError(message) from error
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("OpenAI transcription response was not a JSON object.")
    return data


def draft_case_from_diarized_response(
    *,
    case: dict[str, Any],
    response: Mapping[str, Any],
    provider_output_path: Path,
    workspace: Path,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    response_segments = _response_segments(response)
    provider_ref = _relative_to_workspace(workspace, provider_output_path)
    speaker_ids = _speaker_ids(response_segments)
    speaker_map = {
        speaker: _speaker_record(speaker, person_id=index)
        for index, speaker in enumerate(speaker_ids, start=1)
    }

    segments: list[dict[str, Any]] = []
    for index, raw_segment in enumerate(response_segments, start=1):
        speaker = _raw_speaker(raw_segment)
        speaker_record = speaker_map[speaker]
        start = _round_seconds(raw_segment.get("start", 0.0))
        end = _round_seconds(raw_segment.get("end", start))
        text = str(raw_segment.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            {
                "segment_id": index,
                "start": start,
                "end": end,
                "text": text,
                "true_person_id": speaker_record["person_id"],
                "true_display_name": speaker_record["display_name"],
                "speaker_type": "unknown",
                "evidence_candidates": [
                    {
                        "person_id": speaker_record["person_id"],
                        "display_name": speaker_record["display_name"],
                        "confidence": 0.0,
                        "evidence_types": ["diarized_transcription"],
                        "duration_seconds": max(0.0, _round_seconds(end - start)),
                        "provenance": [f"openai:{model}", provider_ref],
                    }
                ],
                "notes": _segment_notes(raw_segment, model),
            }
        )

    updated = dict(case)
    updated["segments"] = segments
    updated["speakers"] = list(speaker_map.values())
    conditions = dict(updated.get("conditions", {}))
    conditions["speaker_count"] = len(speaker_map)
    conditions["has_unknown_speakers"] = True
    updated["conditions"] = conditions
    updated["annotation"] = _updated_annotation(
        annotation=updated.get("annotation"),
        segments_count=len(segments),
        speakers_count=len(speaker_map),
        provider_ref=provider_ref,
        model=model,
    )
    return updated


def _multipart_form_data(*, fields: Mapping[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = f"----codex-{uuid.uuid4().hex}"
    lines: list[bytes] = []
    for name, value in fields.items():
        lines.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                f"{value}\r\n".encode(),
            ]
        )

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    lines.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; '
                f'filename="{file_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(lines), f"multipart/form-data; boundary={boundary}"


def _response_payload(cached: Mapping[str, Any]) -> Mapping[str, Any]:
    response = cached.get("response", cached)
    if not isinstance(response, Mapping):
        raise ValueError("Cached provider output does not contain a JSON object response.")
    return response


def _response_segments(response: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("segments", "utterances"):
        segments = response.get(key)
        if isinstance(segments, list):
            return [segment for segment in segments if isinstance(segment, Mapping)]
    raise ValueError("Diarized transcription response did not contain segments.")


def _speaker_ids(response_segments: Sequence[Mapping[str, Any]]) -> list[str]:
    speakers: list[str] = []
    for segment in response_segments:
        speaker = _raw_speaker(segment)
        if speaker not in speakers:
            speakers.append(speaker)
    return speakers


def _speaker_record(raw_speaker: str, person_id: int) -> dict[str, Any]:
    return {
        "person_id": person_id,
        "display_name": _speaker_display_name(raw_speaker),
        "speaker_type": "unknown",
        "aliases": [f"openai:{raw_speaker}"],
        "notes": "Machine diarized provisional speaker. Human review required before promotion.",
    }


def _raw_speaker(segment: Mapping[str, Any]) -> str:
    speaker = segment.get("speaker") or segment.get("speaker_id") or segment.get("speaker_label")
    return str(speaker or "unknown").strip()


def _speaker_slug(raw_speaker: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_speaker.strip().lower()).strip("_")
    return f"speaker_{slug or 'unknown'}"


def _speaker_display_name(raw_speaker: str) -> str:
    stripped = raw_speaker.strip()
    if stripped.lower().startswith("speaker"):
        return stripped.replace("_", " ").title()
    return f"Speaker {stripped}".strip()


def _segment_notes(raw_segment: Mapping[str, Any], model: str) -> str:
    raw_id = raw_segment.get("id") or raw_segment.get("segment_id")
    speaker = _raw_speaker(raw_segment)
    parts = [
        "Machine-generated draft from diarized transcription; not human reviewed.",
        f"provider={PROVIDER_NAME}",
        f"model={model}",
        f"provider_speaker={speaker}",
    ]
    if raw_id:
        parts.append(f"provider_segment_id={raw_id}")
    return " ".join(parts)


def _updated_annotation(
    *,
    annotation: object,
    segments_count: int,
    speakers_count: int,
    provider_ref: str,
    model: str,
) -> dict[str, Any]:
    existing = annotation if isinstance(annotation, dict) else {}
    return {
        **existing,
        "status": "draft",
        "review_level": "rough",
        "provider": PROVIDER_NAME,
        "provider_model": model,
        "provider_output": provider_ref,
        "human_review_required": True,
        "notes": (
            f"Machine-populated {segments_count} transcript segments and "
            f"{speakers_count} provisional speakers from {PROVIDER_NAME}. "
            "Speaker identities are anonymous diarization labels until reviewed."
        ),
    }


def _case_media_path(workspace: Path, case: Mapping[str, Any]) -> Path:
    media_uri = case.get("media_uri")
    if not isinstance(media_uri, str):
        media = case.get("media")
        if isinstance(media, Mapping):
            media_uri = media.get("media_uri")
    if not isinstance(media_uri, str):
        raise ValueError(f"Case {case.get('case_id')} does not define media_uri.")

    media_path = Path(media_uri)
    if media_path.is_absolute():
        return media_path
    drafts_path = workspace / "datasets" / "drafts" / media_path
    if drafts_path.exists():
        return drafts_path
    return workspace / media_path


def _audio_cache_path(workspace: Path, case: Mapping[str, Any], media_path: Path) -> Path:
    source_id = _source_id(case)
    return (
        workspace
        / "datasets"
        / "drafts"
        / "media"
        / source_id
        / "audio_segments"
        / f"{media_path.stem}.mp3"
    )


def _provider_output_path(workspace: Path, case: Mapping[str, Any]) -> Path:
    return (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / PROVIDER_NAME
        / f"{case['case_id']}.json"
    )


def _source_id(case: Mapping[str, Any]) -> str:
    source = case.get("source")
    if isinstance(source, Mapping):
        source_id = source.get("source_id")
        if isinstance(source_id, str) and source_id:
            return source_id
    return "unknown_source"


def _relative_to_workspace(workspace: Path, path: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return path.as_posix()


def _round_seconds(value: Any) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return 0.0


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a JSON object.")
    return data


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate draft cases with OpenAI diarized segments."
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--case-glob", default="youtube_gG1Lq2pIgGM_part_*.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    updated = populate_draft_cases(
        workspace=args.workspace,
        case_glob=args.case_glob,
        model=args.model,
        force=args.force,
    )
    print(json.dumps({"updated_cases": [str(path) for path in updated]}, indent=2))


if __name__ == "__main__":
    main()
