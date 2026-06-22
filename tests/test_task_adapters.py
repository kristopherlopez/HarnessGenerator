from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.adapters import resolve_task_adapter
from evals.compare_strategies import compare_strategies
from evals.run_eval import run_eval

SIMPLE_QA_WORKSPACE = Path("tests/fixtures/workspaces/simple_qa")
SIMPLE_QA_DATASET = SIMPLE_QA_WORKSPACE / "datasets" / "tiny"
YOUTUBE_WORKSPACE = Path("workspaces/youtube_speaker_attribution")
YOUTUBE_DATASET = YOUTUBE_WORKSPACE / "datasets" / "small_gold"


def test_simple_qa_eval_runs_without_identity_metrics(tmp_path: Path) -> None:
    report = run_eval(
        SIMPLE_QA_DATASET,
        "baseline_context_answer",
        report_path=tmp_path / "latest.json",
        failure_report_path=tmp_path / "latest_failures.json",
        workspace=SIMPLE_QA_WORKSPACE,
    )

    assert report["task_type"] == "simple_qa"
    assert report["harness_hypothesis"]["task_type"] == "simple_qa"
    assert report["harness_run_summary"]["run_count"] == 1
    assert report["metrics"]["exact_match"] == 1.0
    assert report["metrics"]["malformed_output_rate"] == 0.0
    assert "false_assignment_rate" not in report["metrics"]
    assert report["cases"] == [
        {
            "case_id": "capital_france",
            "strategy": "baseline_context_answer",
            "answer": "Paris",
            "confidence": 1.0,
        }
    ]


def test_simple_qa_strategy_comparison_selects_baseline(tmp_path: Path) -> None:
    report = compare_strategies(
        SIMPLE_QA_DATASET,
        workspace=SIMPLE_QA_WORKSPACE,
        output_path=tmp_path / "strategy_comparison.json",
    )

    assert report["task_type"] == "simple_qa"
    assert report["winner"] == "baseline_context_answer"
    assert "baseline_context_answer" in report["harness_hypotheses"]
    assert report["results"] == [
        {
            "strategy": "baseline_context_answer",
            "metrics": {
                "total_cases": 1.0,
                "exact_match": 1.0,
                "malformed_output_rate": 0.0,
                "latency_ms": 0.0,
            },
            "eligible": True,
        }
    ]


def test_youtube_eval_still_reports_identity_metrics(tmp_path: Path) -> None:
    report = run_eval(
        YOUTUBE_DATASET,
        "review_heavy_low_false_assignment",
        report_path=tmp_path / "latest.json",
        failure_report_path=tmp_path / "latest_failures.json",
        workspace=YOUTUBE_WORKSPACE,
    )

    assert report["task_type"] == "youtube_speaker_attribution"
    assert report["metrics"]["false_assignment_rate"] == 0.0
    assert report["metrics"]["known_person_recall"] == 7 / 9


def test_unknown_workspace_adapter_fails_with_actionable_error(tmp_path: Path) -> None:
    workspace = tmp_path / "unknown_workspace"
    workspace.mkdir()
    (workspace / "task.yaml").write_text(
        yaml.safe_dump({"workspace_id": "unknown_task"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown task adapter 'unknown_task'"):
        resolve_task_adapter(workspace)
