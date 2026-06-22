from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.adapters import resolve_task_adapter
from app.bootstrap.contracts import load_bootstrap_contracts
from app.harness import build_strategy_hypothesis, execute_strategy_case, summarize_run_results
from app.workspaces import resolve_dataset_path, resolve_workspace, workspace_report_path
from app.workspaces.history import (
    append_history_entry,
    build_strategy_comparison_history_entry,
)
from evals.reports import write_json


def compare_strategies(
    dataset: Path,
    workspace: Path | None = None,
    output_path: Path = Path("evals/reports/strategy_comparison.json"),
    record_history: bool = False,
    history_path: Path | None = None,
    loop_name: str = "evaluate_harness_loop",
) -> dict[str, Any]:
    contracts = load_bootstrap_contracts(workspace=workspace)
    adapter = resolve_task_adapter(workspace)
    cases = adapter.load_dataset(dataset)
    results: list[dict[str, Any]] = []
    harness_hypotheses: dict[str, dict[str, Any]] = {}
    harness_run_summaries: dict[str, dict[str, Any]] = {}

    configured = set(contracts.strategy.resolution_strategies)
    for strategy_name, strategy in adapter.available_strategies().items():
        if strategy_name not in configured:
            continue
        hypothesis = build_strategy_hypothesis(
            adapter=adapter,
            strategy_name=strategy_name,
            workspace=workspace,
        )
        executions = [
            execute_strategy_case(
                adapter=adapter,
                strategy=strategy,
                case=case,
                hypothesis=hypothesis,
                dataset=dataset,
                workspace=workspace,
            )
            for case in cases
        ]
        predictions = [execution.prediction for execution in executions]
        run_results = [execution.run_result for execution in executions]
        harness_hypotheses[strategy_name] = hypothesis.model_dump(mode="json")
        harness_run_summaries[strategy_name] = summarize_run_results(run_results)
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
        "harness_hypotheses": harness_hypotheses,
        "harness_run_summaries": harness_run_summaries,
        "results": results,
        "winner": winner,
    }
    write_json(output_path, report)
    if record_history and workspace is not None:
        history_entry = build_strategy_comparison_history_entry(
            workspace=workspace,
            dataset=dataset,
            report=report,
            output_path=output_path,
            loop_name=loop_name,
            history_output_path=history_path,
            harness_hypotheses=harness_hypotheses,
            harness_run_summaries=harness_run_summaries,
        )
        history_output = append_history_entry(workspace, history_entry, output_path=history_path)
        report["history_entry_path"] = str(history_output)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare identity-resolution strategies.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--history-output", type=Path)
    parser.add_argument("--loop", default="evaluate_harness_loop")
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    dataset = resolve_dataset_path(workspace, args.dataset)
    output = args.output or workspace_report_path(
        workspace,
        "strategy_comparison.json",
        Path("evals/reports/strategy_comparison.json"),
    )
    compare_strategies(
        dataset,
        workspace=workspace,
        output_path=output,
        record_history=workspace is not None and not args.no_history,
        history_path=args.history_output,
        loop_name=args.loop,
    )


if __name__ == "__main__":
    main()
