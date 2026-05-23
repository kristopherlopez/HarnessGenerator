from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.adapters import resolve_task_adapter
from app.bootstrap.contracts import load_bootstrap_contracts
from app.workspaces import resolve_dataset_path, resolve_workspace, workspace_report_path
from evals.reports import write_json


def compare_strategies(
    dataset: Path,
    workspace: Path | None = None,
    output_path: Path = Path("evals/reports/strategy_comparison.json"),
) -> dict[str, Any]:
    contracts = load_bootstrap_contracts(workspace=workspace)
    adapter = resolve_task_adapter(workspace)
    cases = adapter.load_dataset(dataset)
    results: list[dict[str, Any]] = []

    configured = set(contracts.strategy.resolution_strategies)
    for strategy_name, strategy in adapter.available_strategies().items():
        if strategy_name not in configured:
            continue
        predictions = [strategy.predict_case(case) for case in cases]
        metrics, _rows = adapter.score_predictions(cases, predictions)
        results.append(
            {
                "strategy": strategy_name,
                "metrics": metrics,
                "eligible": adapter.is_eligible(metrics, contracts.strategy.selection_policy),
            }
        )

    winner = adapter.select_winner(results)
    report = {
        "dataset": str(dataset),
        "task_type": adapter.task_type,
        "selection_policy": contracts.strategy.selection_policy,
        "results": results,
        "winner": winner,
    }
    write_json(output_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare identity-resolution strategies.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    dataset = resolve_dataset_path(workspace, args.dataset)
    output = args.output or workspace_report_path(
        workspace,
        "strategy_comparison.json",
        Path("evals/reports/strategy_comparison.json"),
    )
    compare_strategies(dataset, workspace=workspace, output_path=output)


if __name__ == "__main__":
    main()
