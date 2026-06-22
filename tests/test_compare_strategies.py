from __future__ import annotations

import json
from pathlib import Path

from app.identity.models import EvalCase, EvidenceCandidate, SegmentCase
from app.identity.strategies import ConservativeEvidenceStrategy
from evals.compare_strategies import compare_strategies
from evals.dataset import load_dataset

WORKSPACE = Path("workspaces/youtube_speaker_attribution")


def test_strategy_comparison_rejects_risky_high_accuracy_strategy(tmp_path: Path) -> None:
    report = compare_strategies(
        WORKSPACE / "datasets" / "small_gold",
        workspace=WORKSPACE,
        output_path=tmp_path / "strategy_comparison.json",
    )
    result_by_strategy = {result["strategy"]: result for result in report["results"]}

    assert result_by_strategy["risky_top_candidate"]["eligible"] is False
    assert result_by_strategy["review_heavy_low_false_assignment"]["metrics"][
        "false_assignment_rate"
    ] == 0.0
    assert result_by_strategy["review_heavy_low_false_assignment"]["metrics"][
        "known_person_recall"
    ] == 7 / 9
    assert result_by_strategy["review_heavy_low_false_assignment"]["metrics"][
        "needs_review_rate"
    ] == 0.25
    assert report["winner"] == "review_heavy_low_false_assignment"
    assert report["harness_hypotheses"]["review_heavy_low_false_assignment"][
        "declared_change_surface"
    ] == "registered_strategy"
    assert report["harness_run_summaries"]["review_heavy_low_false_assignment"][
        "run_count"
    ] == 12


def test_strategy_comparison_can_append_workspace_history(tmp_path: Path) -> None:
    history_path = tmp_path / "harness_history.jsonl"
    report = compare_strategies(
        WORKSPACE / "datasets" / "small_gold",
        workspace=WORKSPACE,
        output_path=tmp_path / "strategy_comparison.json",
        record_history=True,
        history_path=history_path,
    )

    assert report["history_entry_path"] == str(history_path)
    entries = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["run_type"] == "strategy_comparison"
    assert entry["harness"]["winner"] == "review_heavy_low_false_assignment"
    assert entry["strategy_results"]
    assert entry["dataset"]["content_sha256"]
    assert "review_heavy_low_false_assignment" in entry["harness_hypotheses"]
    assert entry["harness_run_summaries"]["review_heavy_low_false_assignment"][
        "model_call_count"
    ] == 0


def test_conservative_strategy_resolves_only_safe_voice_only_evidence() -> None:
    strategy = ConservativeEvidenceStrategy()
    cases = load_dataset(WORKSPACE / "datasets" / "small_gold")
    predictions = {
        case.case_id: strategy.predict_case(case).segments[0]
        for case in cases
    }

    voice_only_known = predictions["video_off_camera"]
    assert voice_only_known.resolution_status == "resolved"
    assert voice_only_known.person_id == 1
    assert voice_only_known.evidence_summary.provenance == ["voice_profile:host:v1"]

    assert predictions["short_interjection"].resolution_status == "needs_review"
    assert predictions["short_interjection"].person_id == 0
    assert predictions["similar_voices"].resolution_status == "needs_review"
    assert predictions["similar_voices"].person_id == 0
    assert predictions["similar_voices"].evidence_summary.provenance == [
        "voice_profile:guest_c:v1"
    ]
    assert predictions["similar_voices"].evidence_summary.conflicts == [
        "ambiguous_voice_candidate_margin"
    ]
    assert predictions["audio_unknown_guest"].resolution_status == "unknown"
    assert predictions["panel_overlap"].resolution_status == "unknown"
    assert predictions["high_overlap_active_speaker"].resolution_status == "resolved"
    assert predictions["high_overlap_active_speaker"].person_id == 3
    assert predictions["high_overlap_voice_only_unknown"].resolution_status == "needs_review"
    assert predictions["high_overlap_voice_only_unknown"].person_id == 0


def test_conservative_strategy_applies_review_budget_by_priority() -> None:
    strategy = ConservativeEvidenceStrategy(max_review_rate=0.25, minimum_review_slots=1)
    case = EvalCase(
        case_id="review_budget_case",
        media_uri="mock://review_budget_case.wav",
        known_people_set_id="seed_podcast",
        media_type="audio",
        conditions={
            "speaker_count": 3,
            "has_unknown_speakers": False,
            "overlap_level": "medium",
            "face_visibility": "none",
            "audio_quality": "medium",
        },
        segments=[
            _voice_segment(
                segment_id=1,
                start=0.0,
                end=1.2,
                confidence=0.88,
                runner_up_confidence=None,
            ),
            _voice_segment(
                segment_id=2,
                start=2.0,
                end=8.0,
                confidence=0.91,
                runner_up_confidence=0.90,
            ),
            _voice_segment(
                segment_id=3,
                start=9.0,
                end=15.0,
                confidence=0.83,
                runner_up_confidence=0.82,
            ),
            SegmentCase(
                segment_id=4,
                start=16.0,
                end=20.0,
                text="No usable candidate here.",
                true_person_id=0,
                true_display_name="Unknown Speaker",
                speaker_type="unknown",
                evidence_candidates=[],
            ),
        ],
    )

    prediction_by_segment = {
        prediction.segment_id: prediction
        for prediction in strategy.predict_case(case).segments
    }

    assert prediction_by_segment[2].resolution_status == "needs_review"
    assert prediction_by_segment[2].review.reason == "ambiguous_voice_candidate_margin"
    assert prediction_by_segment[1].resolution_status == "unknown"
    assert prediction_by_segment[1].review.reason == "review_budget_exceeded"
    assert prediction_by_segment[3].resolution_status == "unknown"
    assert prediction_by_segment[3].review.reason == "review_budget_exceeded"
    assert prediction_by_segment[4].resolution_status == "unknown"


def test_conservative_strategy_requires_corroborating_signal_for_high_overlap() -> None:
    strategy = ConservativeEvidenceStrategy()
    case = EvalCase(
        case_id="high_overlap_case",
        media_uri="mock://high_overlap_case.wav",
        known_people_set_id="seed_panel",
        media_type="video",
        conditions={
            "speaker_count": 3,
            "has_unknown_speakers": False,
            "overlap_level": "high",
            "face_visibility": "medium",
            "audio_quality": "medium",
        },
        segments=[
            _voice_segment(
                segment_id=1,
                start=0.0,
                end=6.0,
                confidence=0.93,
                runner_up_confidence=None,
            ),
            _voice_segment(
                segment_id=2,
                start=7.0,
                end=13.0,
                confidence=0.90,
                runner_up_confidence=None,
                evidence_types=["voice", "active_speaker"],
            ),
        ],
    )

    prediction_by_segment = {
        prediction.segment_id: prediction
        for prediction in strategy.predict_case(case).segments
    }

    assert prediction_by_segment[1].resolution_status == "needs_review"
    assert prediction_by_segment[1].person_id == 0
    assert prediction_by_segment[1].review.reason == "candidate_below_safe_assignment_threshold"
    assert prediction_by_segment[2].resolution_status == "resolved"
    assert prediction_by_segment[2].person_id == 1


def _voice_segment(
    segment_id: int,
    start: float,
    end: float,
    confidence: float,
    runner_up_confidence: float | None,
    evidence_types: list[str] | None = None,
) -> SegmentCase:
    resolved_evidence_types = evidence_types or ["voice"]
    provenance = ["voice_profile:known:v1"]
    if "active_speaker" in resolved_evidence_types:
        provenance.append("active_speaker:mock")
    candidates = [
        EvidenceCandidate(
            person_id=1,
            display_name="Known Speaker",
            confidence=confidence,
            evidence_types=resolved_evidence_types,
            duration_seconds=end - start,
            provenance=provenance,
        )
    ]
    if runner_up_confidence is not None:
        candidates.append(
            EvidenceCandidate(
                person_id=2,
                display_name="Runner Up",
                confidence=runner_up_confidence,
                evidence_types=["voice"],
                duration_seconds=end - start,
                provenance=["voice_profile:runner_up:v1"],
            )
        )

    return SegmentCase(
        segment_id=segment_id,
        start=start,
        end=end,
        text=f"Segment {segment_id}.",
        true_person_id=segment_id,
        true_display_name="Known Speaker",
        speaker_type="known",
        evidence_candidates=candidates,
    )
