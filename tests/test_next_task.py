from __future__ import annotations

import json
from pathlib import Path

from app.harness_optimizer.next_task import generate_next_task


def test_generate_next_task_prioritizes_false_assignment(tmp_path: Path) -> None:
    eval_report = tmp_path / "latest.json"
    failure_report = tmp_path / "failures.json"
    output = tmp_path / "next_task.md"

    eval_report.write_text(
        json.dumps(
            {
                "strategy": "risky_top_candidate",
                "metrics": {
                    "false_assignment_rate": 0.2,
                    "identity_accuracy": 0.8,
                    "known_person_recall": 1.0,
                    "needs_review_rate": 0.0,
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
                        "case_id": "short_interjection",
                        "segment_id": 1,
                        "failure_type": "false_assignment",
                        "suspected_cause": "short voice segment accepted",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    generate_next_task(eval_report, failure_report, output)

    task = output.read_text(encoding="utf-8")
    assert "improve false assignment" in task
    assert "short_interjection 1" in task
    assert "Allowed Harness Change Surfaces" in task
    assert "thresholds_and_policies" in task
    assert "contracts/safety_contract.yaml" in task
