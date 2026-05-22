from __future__ import annotations

import json
from pathlib import Path

from app.calibration.seed_gold import (
    build_seed_profile,
    build_seed_profile_from_cases,
    generate_seeded_review_cases,
    promote_case_to_seed_gold,
    promote_seed_case,
)


def test_seed_profile_maps_provider_speakers_from_reviewed_seed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    draft_case_path = workspace / "datasets" / "drafts" / "cases" / "seed.json"
    provider_path = (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / "deepgram_diarized_transcription"
        / "seed.json"
    )
    draft_case_path.parent.mkdir(parents=True)
    provider_path.parent.mkdir(parents=True)

    draft_case_path.write_text(
        json.dumps(
            {
                "case_id": "seed",
                "media_uri": "media/seed.mp4",
                "known_people_set_id": "seed_podcast",
                "media_type": "video",
                "conditions": {},
                "speakers": [
                    {"person_id": 1, "display_name": "Denan Kemp", "speaker_type": "known"},
                    {"person_id": 2, "display_name": "Sandor Earl", "speaker_type": "known"},
                ],
                "segments": [
                    {
                        "segment_id": 1,
                        "start": 0.0,
                        "end": 1.0,
                        "text": "Denan words",
                        "true_person_id": 1,
                        "true_display_name": "Denan Kemp",
                        "speaker_type": "known",
                        "evidence_candidates": [],
                    },
                    {
                        "segment_id": 2,
                        "start": 1.0,
                        "end": 2.0,
                        "text": "Sandor words",
                        "true_person_id": 2,
                        "true_display_name": "Sandor Earl",
                        "speaker_type": "known",
                        "evidence_candidates": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    provider_path.write_text(
        json.dumps(
            {
                "response": {
                    "results": {
                        "utterances": [
                            {
                                "id": "u1",
                                "speaker": 1,
                                "words": [
                                    {
                                        "word": "Denan",
                                        "punctuated_word": "Denan",
                                        "start": 0.0,
                                        "end": 0.5,
                                        "confidence": 0.9,
                                        "speaker": 1,
                                    },
                                    {
                                        "word": "words",
                                        "punctuated_word": "words",
                                        "start": 0.5,
                                        "end": 1.0,
                                        "confidence": 0.9,
                                        "speaker": 1,
                                    },
                                    {
                                        "word": "Sandor",
                                        "punctuated_word": "Sandor",
                                        "start": 1.0,
                                        "end": 1.5,
                                        "confidence": 0.9,
                                        "speaker": 0,
                                    },
                                    {
                                        "word": "words",
                                        "punctuated_word": "words",
                                        "start": 1.5,
                                        "end": 2.0,
                                        "confidence": 0.9,
                                        "speaker": 0,
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    seed_path = promote_seed_case(workspace, seed_case_name="seed.json")
    profile = build_seed_profile(
        workspace,
        seed_case_path=seed_path,
        provider_output_path=provider_path,
        output_path=workspace / "datasets" / "seed_gold" / "calibration" / "seed_profile.json",
    )

    assert profile["provider_speaker_map"]["1"]["person_id"] == 1
    assert profile["provider_speaker_map"]["0"]["person_id"] == 2


def test_generate_seeded_review_cases_splits_on_provider_speaker_change(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    source_case_path = workspace / "datasets" / "drafts" / "cases" / "target.json"
    provider_path = (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / "deepgram_diarized_transcription"
        / "target.json"
    )
    profile_path = workspace / "datasets" / "seed_gold" / "calibration" / "seed_profile.json"
    source_case_path.parent.mkdir(parents=True)
    provider_path.parent.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True)

    source_case_path.write_text(
        json.dumps(
            {
                "case_id": "target",
                "media_uri": "media/target.mp4",
                "known_people_set_id": "seed_podcast",
                "media_type": "video",
                "conditions": {},
                "speakers": [],
                "segments": [],
            }
        ),
        encoding="utf-8",
    )
    provider_path.write_text(
        json.dumps(
            {
                "response": {
                    "results": {
                        "utterances": [
                            {
                                "id": "u2",
                                "speaker": 1,
                                "words": [
                                    {
                                        "word": "Denan",
                                        "punctuated_word": "Denan",
                                        "start": 0.0,
                                        "end": 0.5,
                                        "confidence": 1.0,
                                        "speaker": 1,
                                    },
                                    {
                                        "word": "Sandor",
                                        "punctuated_word": "Sandor",
                                        "start": 0.5,
                                        "end": 1.0,
                                        "confidence": 1.0,
                                        "speaker": 0,
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    profile_path.write_text(
        json.dumps(
            {
                "known_people": [
                    {"person_id": 1, "display_name": "Denan Kemp", "speaker_type": "known"},
                    {"person_id": 2, "display_name": "Sandor Earl", "speaker_type": "known"},
                ],
                "provider_speaker_votes": {
                    "1": [{"person_id": 1, "display_name": "Denan Kemp", "share": 1.0}],
                    "0": [{"person_id": 2, "display_name": "Sandor Earl", "share": 1.0}],
                },
                "provider_speaker_map": {
                    "1": {
                        "person_id": 1,
                        "display_name": "Denan Kemp",
                        "share": 1.0,
                        "status": "mapped",
                    },
                    "0": {
                        "person_id": 2,
                        "display_name": "Sandor Earl",
                        "share": 1.0,
                        "status": "mapped",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    created = generate_seeded_review_cases(
        workspace,
        profile_path=profile_path,
        target_glob="target.json",
    )

    assert len(created) == 1
    review_case = json.loads(created[0].read_text(encoding="utf-8"))
    assert [segment["true_person_id"] for segment in review_case["segments"]] == [1, 2]
    assert [segment["text"] for segment in review_case["segments"]] == ["Denan", "Sandor"]


def test_seed_profile_can_map_against_global_provider_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    seed_case_path = workspace / "datasets" / "seed_gold" / "cases" / "target_part_001.json"
    provider_path = (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / "deepgram_diarized_transcription"
        / "target.json"
    )
    profile_path = workspace / "datasets" / "seed_gold" / "calibration" / "seed_profile.json"
    seed_case_path.parent.mkdir(parents=True)
    provider_path.parent.mkdir(parents=True)

    seed_case_path.write_text(
        json.dumps(
            {
                "case_id": "target_part_001",
                "media_uri": "media/target/segments/target_part_001.mp4",
                "media": {"clip_start": 10.0, "clip_end": 20.0},
                "known_people_set_id": "seed_podcast",
                "media_type": "video",
                "conditions": {},
                "speakers": [
                    {"person_id": 1, "display_name": "Denan Kemp", "speaker_type": "known"},
                ],
                "segments": [
                    {
                        "segment_id": 1,
                        "start": 0.0,
                        "end": 1.0,
                        "text": "Denan words",
                        "true_person_id": 1,
                        "true_display_name": "Denan Kemp",
                        "speaker_type": "known",
                        "evidence_candidates": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    provider_path.write_text(
        json.dumps(
            {
                "response": {
                    "results": {
                        "utterances": [
                            {
                                "id": "u1",
                                "speaker": 4,
                                "words": [
                                    {
                                        "word": "Denan",
                                        "punctuated_word": "Denan",
                                        "start": 10.0,
                                        "end": 10.5,
                                        "confidence": 0.9,
                                        "speaker": 4,
                                    },
                                    {
                                        "word": "words",
                                        "punctuated_word": "words",
                                        "start": 10.5,
                                        "end": 11.0,
                                        "confidence": 0.9,
                                        "speaker": 4,
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    profile = build_seed_profile_from_cases(
        workspace,
        seed_case_paths=[seed_case_path],
        output_path=profile_path,
        provider_case_name="target.json",
    )

    assert profile["provider_speaker_map"]["4"]["person_id"] == 1
    assert profile["mapping_basis"] == "global_seed_gold_word_overlap_duration"


def test_generate_seeded_review_cases_can_slice_global_provider_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source_case_path = workspace / "datasets" / "drafts" / "cases" / "target_part_001.json"
    provider_path = (
        workspace
        / "datasets"
        / "drafts"
        / "provider_outputs"
        / "deepgram_diarized_transcription"
        / "target.json"
    )
    profile_path = workspace / "datasets" / "seed_gold" / "calibration" / "seed_profile.json"
    source_case_path.parent.mkdir(parents=True)
    provider_path.parent.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True)

    source_case_path.write_text(
        json.dumps(
            {
                "case_id": "target_part_001",
                "media_uri": "media/target/segments/target_part_001.mp4",
                "media": {"clip_start": 10.0, "clip_end": 20.0},
                "known_people_set_id": "seed_podcast",
                "media_type": "video",
                "conditions": {},
                "speakers": [],
                "segments": [],
            }
        ),
        encoding="utf-8",
    )
    provider_path.write_text(
        json.dumps(
            {
                "response": {
                    "results": {
                        "utterances": [
                            {
                                "id": "global_u1",
                                "speaker": 4,
                                "words": [
                                    {
                                        "word": "Before",
                                        "punctuated_word": "Before",
                                        "start": 9.0,
                                        "end": 9.5,
                                        "confidence": 1.0,
                                        "speaker": 4,
                                    },
                                    {
                                        "word": "Inside",
                                        "punctuated_word": "Inside",
                                        "start": 10.0,
                                        "end": 10.5,
                                        "confidence": 1.0,
                                        "speaker": 4,
                                    },
                                    {
                                        "word": "After",
                                        "punctuated_word": "After",
                                        "start": 20.5,
                                        "end": 21.0,
                                        "confidence": 1.0,
                                        "speaker": 4,
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    profile_path.write_text(
        json.dumps(
            {
                "known_people": [
                    {"person_id": 1, "display_name": "Denan Kemp", "speaker_type": "known"},
                ],
                "provider_speaker_votes": {
                    "4": [{"person_id": 1, "display_name": "Denan Kemp", "share": 1.0}],
                },
                "provider_speaker_map": {
                    "4": {
                        "person_id": 1,
                        "display_name": "Denan Kemp",
                        "share": 1.0,
                        "status": "mapped",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    created = generate_seeded_review_cases(
        workspace,
        profile_path=profile_path,
        target_glob="target_part_001.json",
        provider_case_name="target.json",
    )

    review_case = json.loads(created[0].read_text(encoding="utf-8"))
    assert [segment["text"] for segment in review_case["segments"]] == ["Inside"]
    assert review_case["segments"][0]["start"] == 0.0
    assert review_case["segments"][0]["end"] == 0.5
    assert review_case["segments"][0]["true_person_id"] == 1


def test_promote_review_can_use_global_seeded_review_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source_path = (
        workspace
        / "datasets"
        / "seeded_review_global"
        / "cases"
        / "target_part_003.json"
    )
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        json.dumps(
            {
                "case_id": "target_part_003",
                "media_uri": "media/target/segments/target_part_003.mp4",
                "known_people_set_id": "seed_podcast",
                "media_type": "video",
                "conditions": {},
                "speakers": [],
                "segments": [
                    {
                        "segment_id": 1,
                        "start": 0.0,
                        "end": 1.0,
                        "text": "Reviewed global segment",
                        "true_person_id": 1,
                        "true_display_name": "Denan Kemp",
                        "speaker_type": "known",
                        "evidence_candidates": [],
                    }
                ],
                "annotation": {"status": "seeded_review"},
            }
        ),
        encoding="utf-8",
    )

    promoted_path = promote_case_to_seed_gold(
        workspace,
        case_name="target_part_003.json",
        source_dataset="seeded_review_global",
    )

    promoted = json.loads(promoted_path.read_text(encoding="utf-8"))
    manifest = json.loads(
        (workspace / "datasets" / "seed_gold" / "manifest.json").read_text(encoding="utf-8")
    )
    assert promoted["annotation"]["status"] == "seed_gold"
    assert promoted["annotation"]["source_dataset"] == "seeded_review_global"
    assert promoted["annotation"]["source_case"] == "target_part_003.json"
    assert manifest["cases"] == ["target_part_003.json"]
