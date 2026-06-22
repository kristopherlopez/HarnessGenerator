from __future__ import annotations

import json
from pathlib import Path

from app.harness_optimizer.compare_generated import compare_generated_candidates


def test_compare_generated_rejects_tie_with_baseline(tmp_path: Path) -> None:
    baseline = _write_report(
        tmp_path / "latest.json",
        strategy="promoted",
        false_assignment_rate=0.0,
        identity_accuracy=0.8,
        known_person_recall=0.7,
        needs_review_rate=0.25,
    )
    candidate = _write_report(
        tmp_path / "generated_candidate_001.json",
        strategy="candidate_001",
        false_assignment_rate=0.0,
        identity_accuracy=0.8,
        known_person_recall=0.7,
        needs_review_rate=0.25,
    )

    report = compare_generated_candidates(
        baseline_report_path=baseline,
        candidate_report_paths=[candidate],
        output_path=tmp_path / "comparison.json",
        workspace=Path("workspaces/youtube_speaker_attribution"),
    )

    assert report["winner"] == "candidate_001"
    assert report["decision"]["action"] == "reject"
    assert report["decision"]["recommendation"] == "generate_follow_up"
    assert report["candidates"][0]["delta_from_baseline"]["identity_accuracy"] == 0.0
    assert report["candidate_outcomes"][0]["outcome"] == "failure"
    assert report["candidate_outcomes"][0]["prediction_verdict"] == "not_declared"


def test_compare_generated_accepts_safe_quality_improvement(tmp_path: Path) -> None:
    baseline = _write_report(
        tmp_path / "latest.json",
        strategy="promoted",
        false_assignment_rate=0.0,
        identity_accuracy=0.8,
        known_person_recall=0.7,
        needs_review_rate=0.25,
    )
    candidate = _write_report(
        tmp_path / "generated_candidate_001.json",
        strategy="candidate_001",
        false_assignment_rate=0.0,
        identity_accuracy=0.85,
        known_person_recall=0.75,
        needs_review_rate=0.25,
    )

    report = compare_generated_candidates(
        baseline_report_path=baseline,
        candidate_report_paths=[candidate],
        output_path=tmp_path / "comparison.json",
        workspace=Path("workspaces/youtube_speaker_attribution"),
    )

    assert report["decision"]["action"] == "accept"
    assert report["decision"]["recommendation"] == "promote_candidate"
    assert report["candidate_outcomes"][0]["outcome"] == "success"


def test_compare_generated_writes_candidate_outcome_artifacts(tmp_path: Path) -> None:
    baseline_failures = _write_failure_report(
        tmp_path / "latest_failures.json",
        strategy="promoted",
        failures=[
            {
                "case_id": "panel_overlap",
                "segment_id": 1,
                "failure_type": "missed_known_identity",
                "resolution_status": "unknown",
                "review_reason": "weak_candidate",
                "suspected_cause": "strategy was too conservative",
            }
        ],
    )
    candidate_failures = _write_failure_report(
        tmp_path / "generated_candidate_001_failures.json",
        strategy="candidate_001",
        failures=[
            {
                "case_id": "panel_overlap",
                "segment_id": 1,
                "failure_type": "missed_known_identity",
                "resolution_status": "unknown",
                "review_reason": "weak_candidate",
                "suspected_cause": "strategy was too conservative",
            },
            {
                "case_id": "poor_lighting",
                "segment_id": 1,
                "failure_type": "missed_known_identity",
                "resolution_status": "unknown",
                "review_reason": "weak_candidate",
                "suspected_cause": "threshold became too strict",
            },
        ],
    )
    baseline = _write_report(
        tmp_path / "latest.json",
        strategy="promoted",
        false_assignment_rate=0.0,
        identity_accuracy=0.8,
        known_person_recall=0.7,
        needs_review_rate=0.25,
        failure_report_path=baseline_failures,
    )
    candidate = _write_report(
        tmp_path / "generated_candidate_001.json",
        strategy="candidate_001",
        false_assignment_rate=0.0,
        identity_accuracy=0.7,
        known_person_recall=0.6,
        needs_review_rate=0.2,
        expected_behavior={
            "known_person_recall": "increase",
            "false_assignment_rate": "must remain 0.0 on small_gold",
        },
        failure_report_path=candidate_failures,
    )

    report = compare_generated_candidates(
        baseline_report_path=baseline,
        candidate_report_paths=[candidate],
        output_path=tmp_path / "comparison.json",
        outcomes_output_path=tmp_path / "outcomes.json",
        outcomes_markdown_output_path=tmp_path / "outcomes.md",
        workspace=Path("workspaces/youtube_speaker_attribution"),
    )

    outcome = report["candidate_outcomes"][0]
    assert outcome["outcome"] == "regression"
    assert outcome["prediction_verdict"] == "falsified"
    assert outcome["failure_count_delta"] == 1
    assert outcome["new_failures"][0]["case_id"] == "poor_lighting"
    assert "narrow or revert" in outcome["next_recommendation"]
    written = json.loads((tmp_path / "outcomes.json").read_text(encoding="utf-8"))
    assert written["candidates"][0]["candidate_id"] == "candidate_001"
    assert "candidate_001 - regression" in (tmp_path / "outcomes.md").read_text(
        encoding="utf-8"
    )


def _write_report(
    path: Path,
    *,
    strategy: str,
    false_assignment_rate: float,
    identity_accuracy: float,
    known_person_recall: float,
    needs_review_rate: float,
    expected_behavior: dict[str, str] | None = None,
    failure_report_path: Path | None = None,
) -> Path:
    path.write_text(
        json.dumps(
            {
                "strategy": strategy,
                "harness_config_path": None,
                "failure_report_path": (
                    failure_report_path.as_posix() if failure_report_path else None
                ),
                "harness_hypothesis": {
                    "declared_change_surface": "thresholds_and_policies",
                    "config": {
                        "harness_id": strategy,
                        "change_surface": "thresholds_and_policies",
                        "change_option": "assignment_threshold",
                        "description": "Test candidate",
                        "candidate": {
                            "failure_type": "missed_known_identity",
                            "required_change": "Tune resolver thresholds.",
                            "rationale": "Synthetic test proposal.",
                        },
                        "expected_behavior": expected_behavior or {},
                    },
                },
                "harness_run_summary": {"run_count": 1, "model_call_count": 0},
                "metrics": {
                    "false_assignment_rate": false_assignment_rate,
                    "identity_accuracy": identity_accuracy,
                    "known_person_recall": known_person_recall,
                    "needs_review_rate": needs_review_rate,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_failure_report(
    path: Path,
    *,
    strategy: str,
    failures: list[dict[str, object]],
) -> Path:
    by_failure_type: dict[str, int] = {}
    for failure in failures:
        failure_type = str(failure["failure_type"])
        by_failure_type[failure_type] = by_failure_type.get(failure_type, 0) + 1
    path.write_text(
        json.dumps(
            {
                "strategy": strategy,
                "failure_count": len(failures),
                "by_failure_type": by_failure_type,
                "failures": failures,
            }
        ),
        encoding="utf-8",
    )
    return path
