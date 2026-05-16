from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.bootstrap.contracts import load_bootstrap_contracts
from app.identity.strategies import available_strategies
from app.workspaces import resolve_dataset_path, resolve_workspace, workspace_report_path
from evals.dataset import load_dataset
from evals.metrics import score_predictions
from evals.reports import write_json


def compare_strategies(
    dataset: Path,
    workspace: Path | None = None,
    output_path: Path = Path("evals/reports/strategy_comparison.json"),
) -> dict[str, Any]:
    contracts = load_bootstrap_contracts(workspace=workspace)
    cases = load_dataset(dataset)
    results: list[dict[str, Any]] = []

    configured = set(contracts.strategy.resolution_strategies)
    for strategy_name, strategy in available_strategies().items():
        if strategy_name not in configured:
            continue
        predictions = [strategy.predict_case(case) for case in cases]
        metrics, _rows = score_predictions(cases, predictions)
        results.append(
            {
                "strategy": strategy_name,
                "metrics": metrics,
                "eligible": _is_eligible(metrics, contracts.strategy.selection_policy),
            }
        )

    winner = _select_winner(results)
    report = {
        "dataset": str(dataset),
        "selection_policy": contracts.strategy.selection_policy,
        "results": results,
        "winner": winner,
    }
    write_json(output_path, report)
    return report


def _is_eligible(metrics: dict[str, float], selection_policy: dict[str, Any]) -> bool:
    constraints = selection_policy.get("constraints", {})
    max_false_assignment = float(constraints.get("max_false_assignment_rate", 1.0))
    max_review = float(constraints.get("max_review_rate", 1.0))
    return (
        metrics["false_assignment_rate"] <= max_false_assignment
        and metrics["needs_review_rate"] <= max_review
    )


def _select_winner(results: list[dict[str, Any]]) -> str | None:
    eligible = [result for result in results if result["eligible"]]
    if not eligible:
        return None
    winner = sorted(
        eligible,
        key=lambda result: (
            result["metrics"]["false_assignment_rate"],
            -result["metrics"]["identity_accuracy"],
            result["metrics"]["needs_review_rate"],
        ),
    )[0]
    return str(winner["strategy"])


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
