from __future__ import annotations

import json
from pathlib import Path

from app.harness_optimizer.candidates import propose_candidates


def test_propose_candidates_uses_phase_allowed_surfaces(tmp_path: Path) -> None:
    eval_report = tmp_path / "latest.json"
    failure_report = tmp_path / "failures.json"
    output = tmp_path / "candidate_proposals.json"
    tasks_dir = tmp_path / "tasks"

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
                        "segment_id": "seg_001",
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
        max_candidates=3,
    )

    allowed = set(report.allowed_change_surfaces)
    assert len(report.proposals) == 3
    assert {proposal.change_surface for proposal in report.proposals} <= allowed
    assert all("contracts/safety_contract.yaml" in p.files_not_to_change for p in report.proposals)
    assert output.exists()
    assert (tasks_dir / "candidate_001.md").exists()
    assert "Harness Change Surface" in (tasks_dir / "candidate_001.md").read_text(
        encoding="utf-8"
    )
