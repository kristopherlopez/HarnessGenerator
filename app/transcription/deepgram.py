from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"
DEFAULT_MODEL = "nova-3"
DEFAULT_DIARIZE_MODEL = "latest"
PROVIDER_NAME = "deepgram_diarized_transcription"


def populate_draft_cases(
    *,
    workspace: Path,
    case_glob: str,
    model: str = DEFAULT_MODEL,
    diarize_model: str = DEFAULT_DIARIZE_MODEL,
    env_file: Path = Path(".env"),
    force: bool = False,
) -> list[Path]:
    load_env_file(env_file)
    cases_dir = workspace / "datasets" / "drafts" / "cases"
    case_paths = sorted(cases_dir.glob(case_glob))
    if not case_paths:
        raise FileNotFoundError(f"No draft cases matched {cases_dir / case_glob}")

    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPGRAM_API_KEY is required for Deepgram transcription.")

    updated_paths: list[Path] = []
    for case_path in case_paths:
        case = _read_json(case_path)
        media_path = _case_media_path(workspace, case)
        audio_path = _audio_cache_path(workspace, case, media_path)
        raw_path = _provider_output_path(workspace, case)

        ensure_audio_for_transcription(media_path=media_path, audio_path=audio_path)
        response: Mapping[str, Any]
        if force or not raw_path.exists():
            response = transcribe_with_deepgram(
                api_key=api_key,
                audio_path=audio_path,
                model=model,
                diarize_model=diarize_model,
            )
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            _write_json(
                raw_path,
                {
                    "provider": PROVIDER_NAME,
                    "model": model,
                    "diarize_model": diarize_model,
                    "case_id": case["case_id"],
                    "media_uri": case.get("media_uri"),
                    "audio_cache_uri": _relative_to_workspace(workspace, audio_path),
                    "response": response,
                },
            )
        else:
            cached = _read_json(raw_path)
            response = _response_payload(cached)

        updated_case = draft_case_from_deepgram_response(
            case=case,
            response=response,
            provider_output_path=raw_path,
            workspace=workspace,
            model=model,
            diarize_model=diarize_model,
        )
        _write_json(case_path, updated_case)
        updated_paths.append(case_path)

    return updated_paths


def load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        os.environ.setdefault(key, _clean_env_value(value.strip()))


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


def transcribe_with_deepgram(
    *,
    api_key: str,
    audio_path: Path,
    model: str,
    diarize_model: str,
) -> dict[str, Any]:
    params = {
        "model": model,
        "diarize_model": diarize_model,
        "utterances": "true",
        "punctuate": "true",
        "smart_format": "true",
        "language": "en",
    }
    request = urllib.request.Request(
        f"{DEEPGRAM_LISTEN_URL}?{urllib.parse.urlencode(params)}",
        data=audio_path.read_bytes(),
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": mimetypes.guess_type(audio_path.name)[0] or "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        message = f"Deepgram transcription failed with HTTP {error.code}: {details}"
        raise RuntimeError(message) from error
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Deepgram transcription response was not a JSON object.")
    return data


def draft_case_from_deepgram_response(
    *,
    case: dict[str, Any],
    response: Mapping[str, Any],
    provider_output_path: Path,
    workspace: Path,
    model: str = DEFAULT_MODEL,
    diarize_model: str = DEFAULT_DIARIZE_MODEL,
) -> dict[str, Any]:
    utterances = _response_utterances(response)
    provider_ref = _relative_to_workspace(workspace, provider_output_path)
    speaker_ids = _speaker_ids(utterances)
    speaker_map = {speaker: _speaker_record(speaker) for speaker in speaker_ids}

    segments: list[dict[str, Any]] = []
    for index, utterance in enumerate(utterances, start=1):
        speaker = _raw_speaker(utterance)
        speaker_record = speaker_map[speaker]
        start = _round_seconds(utterance.get("start", 0.0))
        end = _round_seconds(utterance.get("end", start))
        text = str(utterance.get("transcript") or utterance.get("text") or "").strip()
        if not text:
            continue
        transcript_confidence = _confidence(utterance)
        segments.append(
            {
                "segment_id": f"{case['case_id']}_seg_{index:04d}",
                "start": start,
                "end": end,
                "text": text,
                "true_person_id": speaker_record["person_id"],
                "true_display_name": speaker_record["display_name"],
                "speaker_type": "unknown",
                "confidence": transcript_confidence,
                "evidence_candidates": [
                    {
                        "person_id": speaker_record["person_id"],
                        "display_name": speaker_record["display_name"],
                        "confidence": 0.0,
                        "evidence_types": ["diarized_transcription"],
                        "duration_seconds": max(0.0, _round_seconds(end - start)),
                        "provenance": [f"deepgram:{model}:diarize:{diarize_model}", provider_ref],
                    }
                ],
                "notes": _segment_notes(utterance, model, diarize_model),
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
        diarize_model=diarize_model,
    )
    return updated


def _response_payload(cached: Mapping[str, Any]) -> Mapping[str, Any]:
    response = cached.get("response", cached)
    if not isinstance(response, Mapping):
        raise ValueError("Cached provider output does not contain a JSON object response.")
    return response


def _response_utterances(response: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    results = response.get("results")
    if isinstance(results, Mapping):
        utterances = results.get("utterances")
        if isinstance(utterances, list):
            return [utterance for utterance in utterances if isinstance(utterance, Mapping)]
        words = _response_words(results)
        if words:
            return _utterances_from_words(words)

    utterances = response.get("utterances")
    if isinstance(utterances, list):
        return [utterance for utterance in utterances if isinstance(utterance, Mapping)]

    raise ValueError("Deepgram response did not contain utterances or diarized words.")


def _response_words(results: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    channels = results.get("channels")
    if not isinstance(channels, list) or not channels:
        return []
    first_channel = channels[0]
    if not isinstance(first_channel, Mapping):
        return []
    alternatives = first_channel.get("alternatives")
    if not isinstance(alternatives, list) or not alternatives:
        return []
    first_alternative = alternatives[0]
    if not isinstance(first_alternative, Mapping):
        return []
    words = first_alternative.get("words")
    if not isinstance(words, list):
        return []
    return [word for word in words if isinstance(word, Mapping)]


def _utterances_from_words(words: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for word in words:
        speaker = _raw_speaker(word)
        token = str(word.get("punctuated_word") or word.get("word") or "").strip()
        if not token:
            continue
        if current is None or current["speaker"] != speaker:
            current = {
                "speaker": speaker,
                "start": word.get("start", 0.0),
                "end": word.get("end", 0.0),
                "words": [],
            }
            grouped.append(current)
        current["end"] = word.get("end", current["end"])
        current["words"].append(word)

    for group in grouped:
        group["transcript"] = " ".join(
            str(word.get("punctuated_word") or word.get("word") or "").strip()
            for word in group["words"]
        ).strip()
        group["confidence"] = _average_confidence(group["words"])
    return grouped


def _speaker_ids(utterances: Sequence[Mapping[str, Any]]) -> list[str]:
    speakers: list[str] = []
    for utterance in utterances:
        speaker = _raw_speaker(utterance)
        if speaker not in speakers:
            speakers.append(speaker)
    return speakers


def _speaker_record(raw_speaker: str) -> dict[str, Any]:
    normalized = _speaker_slug(raw_speaker)
    return {
        "person_id": f"provisional_deepgram_{normalized}",
        "display_name": _speaker_display_name(raw_speaker),
        "speaker_type": "unknown",
        "aliases": [f"deepgram:{raw_speaker}"],
        "notes": "Machine diarized provisional speaker. Human review required before promotion.",
    }


def _raw_speaker(segment: Mapping[str, Any]) -> str:
    speaker = segment.get("speaker")
    if speaker is None:
        speaker = segment.get("speaker_id") or segment.get("speaker_label")
    return str(speaker if speaker is not None else "unknown").strip()


def _speaker_slug(raw_speaker: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_speaker.strip().lower()).strip("_")
    return f"speaker_{slug or 'unknown'}"


def _speaker_display_name(raw_speaker: str) -> str:
    stripped = raw_speaker.strip()
    if stripped.lower().startswith("speaker"):
        return stripped.replace("_", " ").title()
    return f"Speaker {stripped}".strip()


def _confidence(utterance: Mapping[str, Any]) -> float:
    confidence = utterance.get("confidence")
    if confidence is not None:
        return _bounded_confidence(confidence)
    words = utterance.get("words")
    if isinstance(words, list):
        return _average_confidence([word for word in words if isinstance(word, Mapping)])
    return 0.0


def _average_confidence(words: Sequence[Mapping[str, Any]]) -> float:
    confidences = [_bounded_confidence(word.get("confidence")) for word in words]
    confidences = [confidence for confidence in confidences if confidence > 0.0]
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 4)


def _bounded_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, min(1.0, confidence)), 4)


def _segment_notes(utterance: Mapping[str, Any], model: str, diarize_model: str) -> str:
    raw_id = utterance.get("id") or utterance.get("utterance_id")
    speaker = _raw_speaker(utterance)
    parts = [
        "Machine-generated draft from Deepgram diarized utterances; not human reviewed.",
        f"provider={PROVIDER_NAME}",
        f"model={model}",
        f"diarize_model={diarize_model}",
        f"provider_speaker={speaker}",
    ]
    if raw_id:
        parts.append(f"provider_utterance_id={raw_id}")
    return " ".join(parts)


def _updated_annotation(
    *,
    annotation: object,
    segments_count: int,
    speakers_count: int,
    provider_ref: str,
    model: str,
    diarize_model: str,
) -> dict[str, Any]:
    existing = annotation if isinstance(annotation, dict) else {}
    return {
        **existing,
        "status": "draft",
        "review_level": "rough",
        "provider": PROVIDER_NAME,
        "provider_model": model,
        "provider_diarize_model": diarize_model,
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


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a JSON object.")
    return data


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate draft cases with Deepgram diarized utterances."
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--case-glob", default="youtube_gG1Lq2pIgGM_part_*.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--diarize-model", default=DEFAULT_DIARIZE_MODEL)
    parser.add_argument("--env-file", default=Path(".env"), type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    updated = populate_draft_cases(
        workspace=args.workspace,
        case_glob=args.case_glob,
        model=args.model,
        diarize_model=args.diarize_model,
        env_file=args.env_file,
        force=args.force,
    )
    print(json.dumps({"updated_cases": [str(path) for path in updated]}, indent=2))


if __name__ == "__main__":
    main()
