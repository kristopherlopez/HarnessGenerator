from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.workspaces import DEFAULT_WORKSPACE, resolve_workspace

DEEPGRAM_PROVIDER = "deepgram_diarized_transcription"
DEFAULT_SEED_CASE = "youtube_gG1Lq2pIgGM_part_000.json"
DEFAULT_TARGET_GLOB = "youtube_gG1Lq2pIgGM_part_*.json"
DEFAULT_PROFILE_NAME = "seed_gold_profile.json"


@dataclass(frozen=True)
class TimedWord:
    text: str
    start: float
    end: float
    confidence: float
    provider_speaker: str
    source_word_index: int = 0

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def midpoint(self) -> float:
        return self.start + (self.duration / 2.0)


@dataclass(frozen=True)
class WordGroup:
    utterance_id: str
    provider_speaker: str
    start_word_index: int
    end_word_index: int
    words: list[TimedWord]


def bootstrap_seeded_review_workflow(
    workspace: Path,
    *,
    seed_case_name: str = DEFAULT_SEED_CASE,
    target_glob: str = DEFAULT_TARGET_GLOB,
    provider_case_name: str | None = None,
    output_dataset: str = "seeded_review",
) -> list[Path]:
    seed_case_path = workspace / "datasets" / "seed_gold" / "cases" / seed_case_name
    if not seed_case_path.exists():
        seed_case_path = promote_seed_case(workspace, seed_case_name=seed_case_name)

    profile_path = _default_profile_path(workspace)
    seed_case_names = _seed_gold_case_names(workspace)
    build_seed_profile_from_manifest(
        workspace,
        output_path=profile_path,
        provider_case_name=provider_case_name,
    )
    return generate_seeded_review_cases(
        workspace,
        profile_path=profile_path,
        target_glob=target_glob,
        exclude_case_names=set(seed_case_names),
        output_dataset=output_dataset,
        provider_case_name=provider_case_name,
    )


def promote_seed_case(
    workspace: Path,
    *,
    seed_case_name: str = DEFAULT_SEED_CASE,
    dataset_name: str = "seed_gold",
) -> Path:
    return promote_case_to_seed_gold(
        workspace,
        case_name=seed_case_name,
        source_dataset="drafts",
        dataset_name=dataset_name,
        review_level="cleaned_seed",
    )


def promote_case_to_seed_gold(
    workspace: Path,
    *,
    case_name: str,
    source_dataset: str,
    dataset_name: str = "seed_gold",
    review_level: str = "gold",
) -> Path:
    source_path = workspace / "datasets" / source_dataset / "cases" / case_name
    if not source_path.exists():
        raise FileNotFoundError(f"Missing source case: {source_path}")

    dataset_root = workspace / "datasets" / dataset_name
    cases_root = dataset_root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)

    seed_case = _read_json(source_path)
    annotation = dict(seed_case.get("annotation") or {})
    annotation.update(
        {
            "status": "seed_gold",
            "review_level": review_level,
            "source_dataset": source_dataset,
            "source_case": case_name,
            "notes": (
                "Human-cleaned seed case used to calibrate speaker rosters, provider "
                "speaker mappings, and review drafts for sibling media chunks."
            ),
        }
    )
    seed_case["annotation"] = annotation

    destination_path = cases_root / case_name
    _write_json(destination_path, seed_case)
    _append_manifest_case(dataset_root / "manifest.json", dataset_name, case_name)
    return destination_path


def build_seed_profile_from_manifest(
    workspace: Path,
    *,
    output_path: Path,
    max_reference_spans_per_person: int = 12,
    min_mapping_share: float = 0.55,
    provider_case_name: str | None = None,
) -> dict[str, Any]:
    seed_case_paths = [
        workspace / "datasets" / "seed_gold" / "cases" / case_name
        for case_name in _seed_gold_case_names(workspace)
    ]
    if not seed_case_paths:
        raise FileNotFoundError("No seed_gold cases are listed in the manifest.")
    return build_seed_profile_from_cases(
        workspace,
        seed_case_paths=seed_case_paths,
        output_path=output_path,
        max_reference_spans_per_person=max_reference_spans_per_person,
        min_mapping_share=min_mapping_share,
        provider_case_name=provider_case_name,
    )


def build_seed_profile_from_cases(
    workspace: Path,
    *,
    seed_case_paths: list[Path],
    output_path: Path,
    max_reference_spans_per_person: int = 12,
    min_mapping_share: float = 0.55,
    provider_case_name: str | None = None,
) -> dict[str, Any]:
    speakers: dict[int, dict[str, Any]] = {}
    votes: dict[str, dict[int, float]] = {}
    reference_spans: list[dict[str, Any]] = []
    provider_outputs: list[Path] = []

    for seed_case_path in seed_case_paths:
        seed_case = _read_json(seed_case_path)
        provider_output_path = _provider_output_path(
            workspace,
            seed_case_path.name,
            provider_case_name=provider_case_name,
        )
        provider_outputs.append(provider_output_path)
        words = _all_provider_words(_load_provider_response(provider_output_path))
        segments = _case_segments(seed_case)
        clip_start = _case_clip_start(seed_case)
        speakers.update(_known_speakers(seed_case))

        for word in words:
            segment = _matching_segment(segments, word, time_offset=clip_start)
            if segment is None:
                continue
            person_id = int(segment["true_person_id"])
            if person_id <= 0:
                continue
            provider_votes = votes.setdefault(word.provider_speaker, {})
            provider_votes[person_id] = provider_votes.get(person_id, 0.0) + word.duration

        reference_spans.extend(
            _reference_spans(
                seed_case,
                words,
                time_offset=clip_start,
                max_reference_spans_per_person=max_reference_spans_per_person,
            )
        )

    provider_speaker_map = _provider_speaker_map(
        votes,
        speakers,
        min_mapping_share=min_mapping_share,
    )
    profile: dict[str, Any] = {
        "schema_version": 1,
        "seed_cases": [_workspace_relative(workspace, path) for path in seed_case_paths],
        "provider_outputs": list(
            dict.fromkeys(_workspace_relative(workspace, path) for path in provider_outputs)
        ),
        "provider": DEEPGRAM_PROVIDER,
        "mapping_basis": (
            "global_seed_gold_word_overlap_duration"
            if provider_case_name
            else "seed_gold_word_overlap_duration"
        ),
        "provider_case_name": provider_case_name,
        "min_mapping_share": min_mapping_share,
        "known_people": list(dict(sorted(speakers.items())).values()),
        "provider_speaker_votes": _serialise_votes(votes, speakers),
        "provider_speaker_map": provider_speaker_map,
        "reference_spans": _limit_reference_spans(
            reference_spans,
            max_reference_spans_per_person=max_reference_spans_per_person,
        ),
    }
    _write_json(output_path, profile)
    return profile


def build_seed_profile(
    workspace: Path,
    *,
    seed_case_path: Path,
    provider_output_path: Path,
    output_path: Path,
    max_reference_spans_per_person: int = 12,
    min_mapping_share: float = 0.55,
    provider_case_name: str | None = None,
) -> dict[str, Any]:
    seed_case = _read_json(seed_case_path)
    words = _all_provider_words(_load_provider_response(provider_output_path))
    segments = _case_segments(seed_case)
    clip_start = _case_clip_start(seed_case) if provider_case_name else 0.0
    speakers = _known_speakers(seed_case)

    votes: dict[str, dict[int, float]] = {}
    for word in words:
        segment = _matching_segment(segments, word, time_offset=clip_start)
        if segment is None:
            continue
        person_id = int(segment["true_person_id"])
        if person_id <= 0:
            continue
        provider_votes = votes.setdefault(word.provider_speaker, {})
        provider_votes[person_id] = provider_votes.get(person_id, 0.0) + word.duration

    provider_speaker_map = _provider_speaker_map(
        votes,
        speakers,
        min_mapping_share=min_mapping_share,
    )
    reference_spans = _reference_spans(
        seed_case,
        words,
        time_offset=clip_start,
        max_reference_spans_per_person=max_reference_spans_per_person,
    )

    profile: dict[str, Any] = {
        "schema_version": 1,
        "seed_case": _workspace_relative(workspace, seed_case_path),
        "provider_output": _workspace_relative(workspace, provider_output_path),
        "provider": DEEPGRAM_PROVIDER,
        "mapping_basis": (
            "global_seed_gold_word_overlap_duration"
            if provider_case_name
            else "seed_gold_word_overlap_duration"
        ),
        "provider_case_name": provider_case_name,
        "min_mapping_share": min_mapping_share,
        "known_people": list(speakers.values()),
        "provider_speaker_votes": _serialise_votes(votes, speakers),
        "provider_speaker_map": provider_speaker_map,
        "reference_spans": reference_spans,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, profile)
    return profile


def generate_seeded_review_cases(
    workspace: Path,
    *,
    profile_path: Path,
    target_glob: str = DEFAULT_TARGET_GLOB,
    exclude_case_names: set[str] | None = None,
    source_dataset: str = "drafts",
    output_dataset: str = "seeded_review",
    provider_case_name: str | None = None,
) -> list[Path]:
    profile = _read_json(profile_path)
    source_root = workspace / "datasets" / source_dataset
    output_root = workspace / "datasets" / output_dataset
    output_cases_root = output_root / "cases"
    output_cases_root.mkdir(parents=True, exist_ok=True)

    excluded = exclude_case_names or set()
    created_paths: list[Path] = []
    for case_path in sorted((source_root / "cases").glob(target_glob)):
        if case_path.name in excluded:
            continue
        provider_output_path = _provider_output_path(
            workspace,
            case_path.name,
            provider_case_name=provider_case_name,
        )
        if not provider_output_path.exists():
            continue
        review_case = _seeded_review_case(
            workspace,
            source_case_path=case_path,
            provider_output_path=provider_output_path,
            profile=profile,
            profile_path=profile_path,
            provider_case_name=provider_case_name,
        )
        output_path = output_cases_root / case_path.name
        _write_json(output_path, review_case)
        created_paths.append(output_path)

    _write_json(
        output_root / "manifest.json",
        {
            "name": output_dataset,
            "description": (
                "Machine-generated review drafts seeded from seed_gold cases. These are "
                "not gold labels."
            ),
            "seed_profile": _workspace_relative(workspace, profile_path),
            "provider_case_name": provider_case_name,
            "cases": [path.name for path in created_paths],
        },
    )
    return created_paths


def _seeded_review_case(
    workspace: Path,
    *,
    source_case_path: Path,
    provider_output_path: Path,
    profile: dict[str, Any],
    profile_path: Path,
    provider_case_name: str | None = None,
) -> dict[str, Any]:
    source_case = _read_json(source_case_path)
    response = _load_provider_response(provider_output_path)
    clip_start = _case_clip_start(source_case) if provider_case_name else None
    clip_end = _case_clip_end(source_case) if provider_case_name else None
    groups = _provider_word_groups(
        response,
        clip_start=clip_start,
        clip_end=clip_end,
        time_shift=clip_start or 0.0,
    )

    segments: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        segments.append(
            _review_segment_from_group(
                index,
                group,
                profile=profile,
                provider_output_path=provider_output_path,
                workspace=workspace,
            )
        )

    annotation = dict(source_case.get("annotation") or {})
    annotation.update(
        {
            "status": "seeded_review",
            "review_level": "machine_seeded",
            "source_case": source_case_path.name,
            "seed_profile": _workspace_relative(workspace, profile_path),
            "provider_output": _workspace_relative(workspace, provider_output_path),
            "provider_case_name": provider_case_name,
            "notes": (
                "Generated from provider word-level speaker changes and the seed_gold "
                "profile. Requires human review before promotion."
            ),
        }
    )

    review_case = dict(source_case)
    review_case["speakers"] = list(profile.get("known_people", []))
    review_case["segments"] = segments
    review_case["annotation"] = annotation
    return review_case


def _review_segment_from_group(
    segment_id: int,
    group: WordGroup,
    *,
    profile: dict[str, Any],
    provider_output_path: Path,
    workspace: Path,
) -> dict[str, Any]:
    start = round(group.words[0].start, 6)
    end = round(group.words[-1].end, 6)
    duration = round(end - start, 6)
    text = " ".join(word.text for word in group.words)
    avg_word_confidence = _average([word.confidence for word in group.words])

    mapped = _mapping_for_provider_speaker(profile, group.provider_speaker)
    person_id = int(mapped.get("person_id", 0))
    display_name = str(mapped.get("display_name", "Unknown Speaker"))
    mapping_share = float(mapped.get("share", 0.0))
    mapping_status = str(mapped.get("status", "unmapped"))
    candidate_confidence = round(avg_word_confidence * mapping_share, 4)

    candidates = _candidate_list(
        profile,
        group.provider_speaker,
        avg_word_confidence=avg_word_confidence,
        duration=duration,
        provider_output_path=provider_output_path,
        workspace=workspace,
    )
    if not candidates and person_id != 0:
        candidates = [
            {
                "person_id": person_id,
                "display_name": display_name,
                "confidence": candidate_confidence,
                "evidence_types": ["diarized_transcription", "seed_provider_speaker_map"],
                "duration_seconds": duration,
                "provenance": [
                    f"deepgram:nova-3:{DEEPGRAM_PROVIDER}",
                    _workspace_relative(workspace, provider_output_path),
                ],
            }
        ]

    if mapping_status != "mapped":
        person_id = 0
        display_name = "Unknown Speaker"

    return {
        "segment_id": segment_id,
        "start": start,
        "end": end,
        "text": text,
        "true_person_id": person_id,
        "true_display_name": display_name,
        "speaker_type": "known" if person_id > 0 else "unknown",
        "confidence": candidate_confidence if person_id > 0 else avg_word_confidence,
        "evidence_candidates": candidates,
        "notes": (
            "Seed-proposed review segment; requires human confirmation. "
            f"provider={DEEPGRAM_PROVIDER} provider_speaker={group.provider_speaker} "
            f"provider_utterance_id={group.utterance_id} "
            f"provider_word_range={group.start_word_index}-{group.end_word_index} "
            f"mapping_status={mapping_status}"
        ),
    }


def _candidate_list(
    profile: dict[str, Any],
    provider_speaker: str,
    *,
    avg_word_confidence: float,
    duration: float,
    provider_output_path: Path,
    workspace: Path,
) -> list[dict[str, Any]]:
    votes = profile.get("provider_speaker_votes", {})
    if not isinstance(votes, dict):
        return []
    speaker_votes = votes.get(provider_speaker, [])
    if not isinstance(speaker_votes, list):
        return []

    candidates: list[dict[str, Any]] = []
    for vote in speaker_votes[:3]:
        if not isinstance(vote, dict):
            continue
        person_id = int(vote.get("person_id", 0))
        if person_id <= 0:
            continue
        share = float(vote.get("share", 0.0))
        candidates.append(
            {
                "person_id": person_id,
                "display_name": str(vote.get("display_name", "Unknown Speaker")),
                "confidence": round(avg_word_confidence * share, 4),
                "evidence_types": ["diarized_transcription", "seed_provider_speaker_map"],
                "duration_seconds": duration,
                "provenance": [
                    f"deepgram:nova-3:{DEEPGRAM_PROVIDER}",
                    _workspace_relative(workspace, provider_output_path),
                ],
            }
        )
    return candidates


def _mapping_for_provider_speaker(profile: dict[str, Any], provider_speaker: str) -> dict[str, Any]:
    mappings = profile.get("provider_speaker_map", {})
    if not isinstance(mappings, dict):
        return {}
    mapping = mappings.get(provider_speaker, {})
    return mapping if isinstance(mapping, dict) else {}


def _provider_speaker_map(
    votes: dict[str, dict[int, float]],
    speakers: dict[int, dict[str, Any]],
    *,
    min_mapping_share: float,
) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for provider_speaker, person_votes in sorted(votes.items()):
        total = sum(person_votes.values())
        if total <= 0:
            continue
        winner_id, winner_duration = max(person_votes.items(), key=lambda item: item[1])
        winner = speakers.get(winner_id, _unknown_person(winner_id))
        share = winner_duration / total
        mapped[provider_speaker] = {
            "person_id": winner_id,
            "display_name": str(winner.get("display_name", f"Person {winner_id}")),
            "duration_seconds": round(winner_duration, 6),
            "total_duration_seconds": round(total, 6),
            "share": round(share, 4),
            "status": "mapped" if share >= min_mapping_share else "ambiguous",
        }
    return mapped


def _serialise_votes(
    votes: dict[str, dict[int, float]],
    speakers: dict[int, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    serialised: dict[str, list[dict[str, Any]]] = {}
    for provider_speaker, person_votes in sorted(votes.items()):
        total = sum(person_votes.values())
        rows: list[dict[str, Any]] = []
        for person_id, duration in sorted(
            person_votes.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            speaker = speakers.get(person_id, _unknown_person(person_id))
            rows.append(
                {
                    "person_id": person_id,
                    "display_name": str(speaker.get("display_name", f"Person {person_id}")),
                    "duration_seconds": round(duration, 6),
                    "share": round(duration / total, 4) if total > 0 else 0.0,
                }
            )
        serialised[provider_speaker] = rows
    return serialised


def _reference_spans(
    seed_case: dict[str, Any],
    words: list[TimedWord],
    *,
    time_offset: float = 0.0,
    max_reference_spans_per_person: int,
) -> list[dict[str, Any]]:
    speakers = _known_speakers(seed_case)
    by_person: dict[int, list[dict[str, Any]]] = {}

    for segment in _case_segments(seed_case):
        person_id = int(segment["true_person_id"])
        if person_id <= 0:
            continue
        start = float(segment["start"])
        end = float(segment["end"])
        duration = round(end - start, 6)
        if duration < 0.5:
            continue
        absolute_start = start + time_offset
        absolute_end = end + time_offset
        speaker = speakers.get(person_id, _unknown_person(person_id))
        by_person.setdefault(person_id, []).append(
            {
                "person_id": person_id,
                "display_name": str(speaker.get("display_name", f"Person {person_id}")),
                "case_id": str(seed_case.get("case_id", "")),
                "segment_id": segment["segment_id"],
                "start": start,
                "end": end,
                "absolute_start": round(absolute_start, 6),
                "absolute_end": round(absolute_end, 6),
                "duration_seconds": duration,
                "text": str(segment.get("text", "")),
                "provider_speakers": _provider_speaker_durations(
                    words,
                    absolute_start,
                    absolute_end,
                ),
            }
        )

    references: list[dict[str, Any]] = []
    for spans in by_person.values():
        references.extend(
            sorted(spans, key=lambda item: float(item["duration_seconds"]), reverse=True)[
                :max_reference_spans_per_person
            ]
        )
    return sorted(
        references,
        key=lambda item: (int(item["person_id"]), -float(item["duration_seconds"])),
    )


def _limit_reference_spans(
    spans: list[dict[str, Any]],
    *,
    max_reference_spans_per_person: int,
) -> list[dict[str, Any]]:
    by_person: dict[int, list[dict[str, Any]]] = {}
    for span in spans:
        by_person.setdefault(int(span["person_id"]), []).append(span)

    limited: list[dict[str, Any]] = []
    for _person_id, person_spans in sorted(by_person.items()):
        limited.extend(
            sorted(
                person_spans,
                key=lambda item: float(item["duration_seconds"]),
                reverse=True,
            )[:max_reference_spans_per_person]
        )
    return sorted(
        limited,
        key=lambda item: (int(item["person_id"]), -float(item["duration_seconds"])),
    )


def _provider_speaker_durations(
    words: list[TimedWord],
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    durations: dict[str, float] = {}
    for word in words:
        if start <= word.midpoint <= end:
            durations[word.provider_speaker] = (
                durations.get(word.provider_speaker, 0.0) + word.duration
            )
    return [
        {"provider_speaker": speaker, "duration_seconds": round(duration, 6)}
        for speaker, duration in sorted(durations.items(), key=lambda item: item[1], reverse=True)
    ]


def _provider_word_groups(
    response: dict[str, Any],
    *,
    clip_start: float | None = None,
    clip_end: float | None = None,
    time_shift: float = 0.0,
) -> list[WordGroup]:
    groups: list[WordGroup] = []
    for utterance in _utterances(response):
        words = _words_from_utterance(
            utterance,
            clip_start=clip_start,
            clip_end=clip_end,
            time_shift=time_shift,
        )
        if not words:
            continue
        utterance_id = str(utterance.get("id", ""))
        current_speaker = words[0].provider_speaker
        current_words: list[TimedWord] = []
        start_index = words[0].source_word_index
        for word in words:
            if current_words and word.provider_speaker != current_speaker:
                groups.append(
                    WordGroup(
                        utterance_id=utterance_id,
                        provider_speaker=current_speaker,
                        start_word_index=start_index,
                        end_word_index=current_words[-1].source_word_index,
                        words=current_words,
                    )
                )
                current_speaker = word.provider_speaker
                current_words = []
                start_index = word.source_word_index
            current_words.append(word)
        if current_words:
            groups.append(
                WordGroup(
                    utterance_id=utterance_id,
                    provider_speaker=current_speaker,
                    start_word_index=start_index,
                    end_word_index=current_words[-1].source_word_index,
                    words=current_words,
                )
            )
    return groups


def _all_provider_words(response: dict[str, Any]) -> list[TimedWord]:
    words: list[TimedWord] = []
    for utterance in _utterances(response):
        words.extend(_words_from_utterance(utterance))
    return words


def _words_from_utterance(
    utterance: dict[str, Any],
    *,
    clip_start: float | None = None,
    clip_end: float | None = None,
    time_shift: float = 0.0,
) -> list[TimedWord]:
    raw_words = utterance.get("words", [])
    if not isinstance(raw_words, list):
        return []
    utterance_speaker = str(utterance.get("speaker", "unknown"))
    words: list[TimedWord] = []
    for word_index, raw_word in enumerate(raw_words, start=1):
        if not isinstance(raw_word, dict):
            continue
        text = str(raw_word.get("punctuated_word") or raw_word.get("word") or "")
        if not text:
            continue
        raw_start = float(raw_word["start"])
        raw_end = float(raw_word["end"])
        midpoint = raw_start + ((raw_end - raw_start) / 2.0)
        if clip_start is not None and midpoint < clip_start:
            continue
        if clip_end is not None and midpoint >= clip_end:
            continue
        start = raw_start - time_shift
        end = raw_end - time_shift
        if clip_start is not None:
            start = max(0.0, start)
        if clip_end is not None:
            end = min(max(0.0, clip_end - time_shift), end)
        words.append(
            TimedWord(
                text=text,
                start=start,
                end=end,
                confidence=float(raw_word.get("confidence", 0.0)),
                provider_speaker=str(raw_word.get("speaker", utterance_speaker)),
                source_word_index=word_index,
            )
        )
    return words


def _utterances(response: dict[str, Any]) -> list[dict[str, Any]]:
    results = response.get("results", {})
    if not isinstance(results, dict):
        return []
    raw_utterances = results.get("utterances", [])
    if not isinstance(raw_utterances, list):
        return []
    return [utterance for utterance in raw_utterances if isinstance(utterance, dict)]


def _case_segments(case: dict[str, Any]) -> list[dict[str, Any]]:
    raw_segments = case.get("segments", [])
    if not isinstance(raw_segments, list):
        return []
    return [segment for segment in raw_segments if isinstance(segment, dict)]


def _matching_segment(
    segments: list[dict[str, Any]],
    word: TimedWord,
    *,
    time_offset: float = 0.0,
) -> dict[str, Any] | None:
    for segment in segments:
        start = float(segment["start"]) + time_offset
        end = float(segment["end"]) + time_offset
        if start <= word.midpoint <= end:
            return segment
    return None


def _case_clip_start(case: dict[str, Any]) -> float:
    media = case.get("media")
    if isinstance(media, dict):
        return _safe_float(media.get("clip_start"), default=0.0)
    return 0.0


def _case_clip_end(case: dict[str, Any]) -> float | None:
    media = case.get("media")
    if not isinstance(media, dict):
        return None
    value = media.get("clip_end")
    if value is None:
        return None
    return _safe_float(value, default=0.0)


def _known_speakers(case: dict[str, Any]) -> dict[int, dict[str, Any]]:
    known: dict[int, dict[str, Any]] = {}
    raw_speakers = case.get("speakers", [])
    if isinstance(raw_speakers, list):
        for speaker in raw_speakers:
            if isinstance(speaker, dict) and speaker.get("person_id") is not None:
                person_id = int(speaker["person_id"])
                if person_id > 0:
                    known[person_id] = dict(speaker)
    for segment in _case_segments(case):
        person_id = int(segment.get("true_person_id", 0))
        if person_id > 0 and person_id not in known:
            known[person_id] = {
                "person_id": person_id,
                "display_name": str(segment.get("true_display_name", f"Person {person_id}")),
                "speaker_type": "known",
                "aliases": [],
                "notes": "Derived from seed segment labels.",
            }
    return dict(sorted(known.items()))


def _unknown_person(person_id: int) -> dict[str, Any]:
    return {
        "person_id": person_id,
        "display_name": f"Person {person_id}",
        "speaker_type": "unknown",
        "aliases": [],
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _provider_output_path(
    workspace: Path,
    case_filename: str,
    *,
    provider_case_name: str | None = None,
) -> Path:
    return (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / DEEPGRAM_PROVIDER
        / (provider_case_name or case_filename)
    )


def _default_profile_path(workspace: Path) -> Path:
    return workspace / "datasets" / "seed_gold" / "calibration" / DEFAULT_PROFILE_NAME


def _seed_gold_case_names(workspace: Path) -> list[str]:
    manifest_path = workspace / "datasets" / "seed_gold" / "manifest.json"
    if not manifest_path.exists():
        return []
    manifest = _read_json(manifest_path)
    cases = manifest.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"{manifest_path} must contain a 'cases' list")
    return [str(case_name) for case_name in cases]


def _append_manifest_case(path: Path, dataset_name: str, case_name: str) -> None:
    if path.exists():
        manifest = _read_json(path)
    else:
        manifest = {
            "name": dataset_name,
            "description": "Human-cleaned seed cases used for calibration before broader review.",
            "cases": [],
        }

    manifest["name"] = dataset_name
    manifest["description"] = "Human-cleaned seed cases used for calibration before broader review."
    cases = manifest.setdefault("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"{path} must contain a 'cases' list")
    if case_name not in cases:
        cases.append(case_name)
    _write_json(path, manifest)


def _load_provider_response(path: Path) -> dict[str, Any]:
    raw = _read_json(path)
    response = raw.get("response")
    if isinstance(response, dict):
        return response
    return raw


def _workspace_relative(workspace: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return raw


def _safe_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote a cleaned seed case and generate seeded review drafts."
    )
    subparsers = parser.add_subparsers(dest="command")

    bootstrap = subparsers.add_parser("bootstrap", help="Run the full seeded review workflow.")
    bootstrap.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    bootstrap.add_argument("--seed-case", default=DEFAULT_SEED_CASE)
    bootstrap.add_argument("--target-glob", default=DEFAULT_TARGET_GLOB)
    bootstrap.add_argument("--provider-case")
    bootstrap.add_argument("--output-dataset", default="seeded_review")

    promote = subparsers.add_parser("promote", help="Copy a cleaned draft into seed_gold.")
    promote.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    promote.add_argument("--seed-case", default=DEFAULT_SEED_CASE)

    promote_review = subparsers.add_parser(
        "promote-review",
        help="Copy a corrected seeded review case into seed_gold.",
    )
    promote_review.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    promote_review.add_argument("--source-dataset", default="seeded_review")
    promote_review.add_argument("case_name")

    profile = subparsers.add_parser("profile", help="Build a calibration profile from seed_gold.")
    profile.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    profile.add_argument("--provider-case")

    generate = subparsers.add_parser("generate-review", help="Generate seeded review cases.")
    generate.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    generate.add_argument("--target-glob", default=DEFAULT_TARGET_GLOB)
    generate.add_argument("--provider-case")
    generate.add_argument("--output-dataset", default="seeded_review")

    args = parser.parse_args()
    command = args.command or "bootstrap"
    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise ValueError("workspace is required")

    if command == "promote":
        path = promote_seed_case(workspace, seed_case_name=args.seed_case)
        print(path)
        return

    if command == "promote-review":
        path = promote_case_to_seed_gold(
            workspace,
            case_name=args.case_name,
            source_dataset=args.source_dataset,
            review_level="gold",
        )
        print(path)
        return

    profile_path = _default_profile_path(workspace)

    if command == "profile":
        build_seed_profile_from_manifest(
            workspace,
            output_path=profile_path,
            provider_case_name=args.provider_case,
        )
        print(profile_path)
        return

    if command == "generate-review":
        if not profile_path.exists():
            build_seed_profile_from_manifest(
                workspace,
                output_path=profile_path,
                provider_case_name=args.provider_case,
            )
        paths = generate_seeded_review_cases(
            workspace,
            profile_path=profile_path,
            target_glob=args.target_glob,
            exclude_case_names=set(_seed_gold_case_names(workspace)),
            output_dataset=args.output_dataset,
            provider_case_name=args.provider_case,
        )
        for path in paths:
            print(path)
        return

    paths = bootstrap_seeded_review_workflow(
        workspace,
        seed_case_name=args.seed_case,
        target_glob=args.target_glob,
        provider_case_name=args.provider_case,
        output_dataset=args.output_dataset,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
