from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.adapters import default_strategy_name, resolve_task_adapter
from app.harness import (
    build_strategy_hypothesis,
    execute_strategy_case,
    load_harness_config,
    summarize_run_results,
)
from app.workspaces import (
    resolve_dataset_path,
    resolve_harness_path,
    resolve_workspace,
    workspace_report_path,
)
from app.workspaces.history import append_history_entry, build_eval_history_entry
from evals.reports import write_json


def run_eval(
    dataset: Path,
    strategy_name: str | None,
    report_path: Path = Path("evals/reports/latest.json"),
    failure_report_path: Path = Path("evals/failures/latest_failures.json"),
    workspace: Path | None = None,
    record_history: bool = False,
    history_path: Path | None = None,
    loop_name: str = "evaluate_harness_loop",
    harness_path: Path | None = None,
) -> dict[str, Any]:
    adapter = resolve_task_adapter(workspace)
    harness_config: dict[str, Any] | None = None
    if harness_path is None:
        if strategy_name is None:
            raise ValueError("strategy_name is required when harness_path is not provided")
        strategies = adapter.available_strategies()
        if strategy_name not in strategies:
            names = ", ".join(sorted(strategies))
            raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {names}")
        strategy = strategies[strategy_name]
        declared_change_surface = "registered_strategy"
        hypothesis_harness_id = None
        hypothesis_version = "registered-strategy-v1"
    else:
        harness_config = load_harness_config(harness_path)
        strategy = adapter.strategy_from_harness_config(harness_config)
        strategy_name = strategy.name
        declared_change_surface = str(harness_config.get("change_surface", "generated_harness"))
        hypothesis_harness_id = f"{adapter.task_type}:{strategy_name}"
        hypothesis_version = str(harness_config.get("schema_version", "harness-config-v1"))

    cases = adapter.load_dataset(dataset)
    hypothesis = build_strategy_hypothesis(
        adapter=adapter,
        strategy_name=strategy_name,
        workspace=workspace,
        harness_id=hypothesis_harness_id,
        version=hypothesis_version,
        declared_change_surface=declared_change_surface,
        config=harness_config or {},
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
    run_summary = summarize_run_results(run_results)
    harness_hypothesis_payload: dict[str, Any] = hypothesis.model_dump(mode="json")
    harness_run_result_payloads: list[dict[str, Any]] = [
        run_result.model_dump(mode="json") for run_result in run_results
    ]
    metrics, rows = adapter.score_predictions(cases, predictions)
    failure_report = adapter.build_failure_report(strategy_name, rows)

    report: dict[str, Any] = {
        "dataset": str(dataset),
        "strategy": strategy_name,
        "task_type": adapter.task_type,
        "harness_config_path": str(harness_path) if harness_path is not None else None,
        "harness_hypothesis": harness_hypothesis_payload,
        "harness_run_results": harness_run_result_payloads,
        "harness_run_summary": run_summary,
        "metrics": metrics,
        "cases": [adapter.serialize_prediction(prediction) for prediction in predictions],
        "failure_report_path": str(failure_report_path),
    }
    write_json(report_path, report)
    write_json(failure_report_path, failure_report)
    if record_history and workspace is not None:
        history_entry = build_eval_history_entry(
            workspace=workspace,
            dataset=dataset,
            strategy_name=strategy_name,
            metrics=metrics,
            failure_report=failure_report,
            report_path=report_path,
            failure_report_path=failure_report_path,
            loop_name=loop_name,
            history_output_path=history_path,
            harness_config_path=harness_path,
            harness_hypothesis=harness_hypothesis_payload,
            harness_run_summary=run_summary,
        )
        history_output = append_history_entry(workspace, history_entry, output_path=history_path)
        report["history_entry_path"] = str(history_output)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a workspace eval.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--strategy")
    parser.add_argument("--harness", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--failure-output", type=Path)
    parser.add_argument("--history-output", type=Path)
    parser.add_argument("--loop", default="evaluate_harness_loop")
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    dataset = resolve_dataset_path(workspace, args.dataset)
    harness_path = resolve_harness_path(workspace, args.harness)
    strategy_name = args.strategy or (
        None if harness_path is not None else default_strategy_name(workspace)
    )
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
    run_eval(
        dataset,
        strategy_name,
        report_path,
        failure_report_path,
        workspace=workspace,
        record_history=workspace is not None and not args.no_history,
        history_path=args.history_output,
        loop_name=args.loop,
        harness_path=harness_path,
    )


if __name__ == "__main__":
    main()
