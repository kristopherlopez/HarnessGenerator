from __future__ import annotations

from dataclasses import dataclass

from app.identity.models import CasePrediction, EvalCase, PersonId, SegmentId, SegmentPrediction

UNKNOWN_PERSON_ID = 0


@dataclass(frozen=True)
class SegmentScoringRow:
    case_id: str
    segment_id: SegmentId
    true_person_id: PersonId
    predicted_person_id: PersonId
    resolution_status: str
    review_reason: str
    evidence_conflicts: list[str]
    evidence_provenance: list[str]
    is_false_assignment: bool
    is_correct_identity: bool
    failure_type: str | None
    condition: dict[str, object]


def score_predictions(
    cases: list[EvalCase],
    predictions: list[CasePrediction],
) -> tuple[dict[str, float], list[SegmentScoringRow]]:
    case_by_id = {case.case_id: case for case in cases}
    rows: list[SegmentScoringRow] = []

    for case_prediction in predictions:
        case = case_by_id[case_prediction.case_id]
        truth_by_segment = {segment.segment_id: segment for segment in case.segments}
        for prediction in case_prediction.segments:
            truth = truth_by_segment[prediction.segment_id]
            rows.append(_score_segment(case, truth.true_person_id, prediction))

    total = len(rows)
    if total == 0:
        raise ValueError("Cannot score an empty prediction set")

    known_total = sum(1 for row in rows if row.true_person_id != UNKNOWN_PERSON_ID)
    unknown_total = sum(1 for row in rows if row.true_person_id == UNKNOWN_PERSON_ID)
    resolved_total = sum(1 for row in rows if row.resolution_status == "resolved")
    correct_resolved_known = sum(
        1
        for row in rows
        if row.true_person_id != UNKNOWN_PERSON_ID
        and row.resolution_status == "resolved"
        and row.predicted_person_id == row.true_person_id
    )
    false_assignments = sum(1 for row in rows if row.is_false_assignment)
    needs_review = sum(1 for row in rows if row.resolution_status == "needs_review")
    unknown_correct = sum(
        1
        for row in rows
        if row.true_person_id == UNKNOWN_PERSON_ID
        and row.resolution_status in {"unknown", "needs_review"}
    )

    metrics = {
        "total_segments": float(total),
        "identity_accuracy": sum(1 for row in rows if row.is_correct_identity) / total,
        "false_assignment_rate": false_assignments / total,
        "known_person_precision": (
            correct_resolved_known / resolved_total if resolved_total else 0.0
        ),
        "known_person_recall": correct_resolved_known / known_total if known_total else 0.0,
        "unknown_detection_recall": unknown_correct / unknown_total if unknown_total else 1.0,
        "false_merge_rate": 0.0,
        "false_split_rate": 0.0,
        "needs_review_rate": needs_review / total,
        "latency_seconds_per_media_hour": 0.0,
    }
    return metrics, rows


def _score_segment(
    case: EvalCase,
    true_person_id: PersonId,
    prediction: SegmentPrediction,
) -> SegmentScoringRow:
    predicted_person_id = prediction.person_id
    resolved = prediction.resolution_status == "resolved"
    is_false_assignment = resolved and predicted_person_id != true_person_id
    is_correct_identity = (
        predicted_person_id == true_person_id
        if true_person_id != UNKNOWN_PERSON_ID
        else prediction.resolution_status in {"unknown", "needs_review"}
    )
    failure_type: str | None = None
    if is_false_assignment:
        failure_type = "false_assignment"
    elif true_person_id != UNKNOWN_PERSON_ID and prediction.resolution_status != "resolved":
        failure_type = "missed_known_identity"
    elif true_person_id == UNKNOWN_PERSON_ID and prediction.resolution_status == "resolved":
        failure_type = "unknown_forced_to_known"

    return SegmentScoringRow(
        case_id=case.case_id,
        segment_id=prediction.segment_id,
        true_person_id=true_person_id,
        predicted_person_id=predicted_person_id,
        resolution_status=prediction.resolution_status,
        review_reason=prediction.review.reason,
        evidence_conflicts=prediction.evidence_summary.conflicts,
        evidence_provenance=prediction.evidence_summary.provenance,
        is_false_assignment=is_false_assignment,
        is_correct_identity=is_correct_identity,
        failure_type=failure_type,
        condition=case.conditions,
    )
