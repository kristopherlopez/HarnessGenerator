from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.adapters import default_strategy_name, resolve_task_adapter
from app.workspaces import resolve_dataset_path, resolve_workspace, workspace_report_path
from evals.reports import write_json


def run_eval(
    dataset: Path,
    strategy_name: str,
    report_path: Path = Path("evals/reports/latest.json"),
    failure_report_path: Path = Path("evals/failures/latest_failures.json"),
    workspace: Path | None = None,
) -> dict[str, Any]:
    adapter = resolve_task_adapter(workspace)
    strategies = adapter.available_strategies()
    if strategy_name not in strategies:
        names = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {names}")

    cases = adapter.load_dataset(dataset)
    strategy = strategies[strategy_name]
    predictions = [strategy.predict_case(case) for case in cases]
    metrics, rows = adapter.score_predictions(cases, predictions)
    failure_report = adapter.build_failure_report(strategy_name, rows)

    report = {
        "dataset": str(dataset),
        "strategy": strategy_name,
        "task_type": adapter.task_type,
        "metrics": metrics,
        "cases": [adapter.serialize_prediction(prediction) for prediction in predictions],
        "failure_report_path": str(failure_report_path),
    }
    write_json(report_path, report)
    write_json(failure_report_path, failure_report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a workspace eval.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--strategy")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--failure-output", type=Path)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    dataset = resolve_dataset_path(workspace, args.dataset)
    strategy_name = args.strategy or default_strategy_name(workspace)
    report_path = args.output or workspace_report_path(
        workspace,
        "latest.json",
        Path("evals/reports/latest.json"),
    )
    failure_report_path = args.failure_output or workspace_report_path(
        workspace,
        "latest_failures.json",
        Path("evals/failures/latest_failures.json"),
    )
    run_eval(dataset, strategy_name, report_path, failure_report_path, workspace=workspace)


if __name__ == "__main__":
    main()
