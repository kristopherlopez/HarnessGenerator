from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.harness_optimizer.candidates import propose_candidates
from evals.run_eval import run_eval


def test_propose_candidates_uses_phase_allowed_surfaces(tmp_path: Path) -> None:
    eval_report = tmp_path / "latest.json"
    failure_report = tmp_path / "failures.json"
    output = tmp_path / "candidate_proposals.json"
    tasks_dir = tmp_path / "tasks"
    harnesses_dir = tmp_path / "generated_harnesses"

    eval_report.write_text(
        json.dumps(
            {
                "strategy": "review_heavy_low_false_assignment",
                "metrics": {
                    "false_assignment_rate": 0.0,
                    "identity_accuracy": 0.7,
                    "known_person_recall": 0.625,
                    "needs_review_rate": 0.1,
                },
            }
        ),
        encoding="utf-8",
    )
    failure_report.write_text(
        json.dumps(
            {
                "failures": [
                    {
                        "case_id": "video_off_camera",
                        "segment_id": 1,
                        "failure_type": "missed_known_identity",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = propose_candidates(
        eval_report_path=eval_report,
        failure_report_path=failure_report,
        output_path=output,
        tasks_dir=tasks_dir,
        harnesses_dir=harnesses_dir,
        max_candidates=3,
    )

    allowed = set(report.allowed_change_surfaces)
    assert len(report.proposals) == 3
    assert {proposal.change_surface for proposal in report.proposals} <= allowed
    assert report.proposals[0].harness_hypothesis.harness_id == "generic:candidate_001"
    assert (
        report.proposals[0].harness_hypothesis.declared_change_surface
        == report.proposals[0].change_surface
    )
    assert report.proposals[0].harness_artifact == (
        harnesses_dir / "candidate_001" / "harness.yaml"
    ).as_posix()
    assert all("contracts/safety_contract.yaml" in p.files_not_to_change for p in report.proposals)
    assert output.exists()
    harness_config = yaml.safe_load(
        (harnesses_dir / "candidate_001" / "harness.yaml").read_text(encoding="utf-8")
    )
    assert harness_config["status"] == "generated_candidate"
    assert harness_config["strategy_type"] == "conservative_evidence"
    assert harness_config["resolver_config"]["min_voice_only_duration_seconds"] == 3.0
    assert (tasks_dir / "candidate_001.md").exists()
    assert "Harness Change Surface" in (tasks_dir / "candidate_001.md").read_text(
        encoding="utf-8"
    )


def test_generated_candidate_harness_can_run_eval(tmp_path: Path) -> None:
    eval_report = tmp_path / "latest.json"
    failure_report = tmp_path / "failures.json"
    output = tmp_path / "candidate_proposals.json"
    tasks_dir = tmp_path / "tasks"
    harnesses_dir = tmp_path / "generated_harnesses"
    workspace = Path("workspaces/youtube_speaker_attribution")

    eval_report.write_text(
        json.dumps(
            {
                "strategy": "review_heavy_low_false_assignment",
                "metrics": {
                    "false_assignment_rate": 0.0,
                    "identity_accuracy": 0.7,
                    "known_person_recall": 0.625,
                    "needs_review_rate": 0.1,
                },
            }
        ),
        encoding="utf-8",
    )
    failure_report.write_text(
        json.dumps(
            {
                "failures": [
                    {
                        "case_id": "video_off_camera",
                        "segment_id": 1,
                        "failure_type": "missed_known_identity",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = propose_candidates(
        eval_report_path=eval_report,
        failure_report_path=failure_report,
        output_path=output,
        tasks_dir=tasks_dir,
        harnesses_dir=harnesses_dir,
        max_candidates=1,
        workspace=workspace,
    )

    harness_path = Path(str(report.proposals[0].harness_artifact))
    eval_result = run_eval(
        workspace / "datasets" / "small_gold",
        None,
        report_path=tmp_path / "generated_latest.json",
        failure_report_path=tmp_path / "generated_failures.json",
        workspace=workspace,
        harness_path=harness_path,
    )

    assert eval_result["strategy"] == "candidate_001"
    assert eval_result["harness_config_path"] == str(harness_path)
    assert eval_result["harness_hypothesis"]["declared_change_surface"] == "evidence_strategy"
    assert eval_result["harness_run_summary"]["run_count"] == 12
    assert eval_result["metrics"]["false_assignment_rate"] == 0.0
