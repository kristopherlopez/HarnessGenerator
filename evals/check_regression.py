from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.bootstrap.contracts import load_bootstrap_contracts
from app.workspaces import resolve_workspace, workspace_report_path


def check_regression(report_path: Path, workspace: Path | None = None) -> None:
    contracts = load_bootstrap_contracts(workspace=workspace)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = report["metrics"]
    constraints = contracts.strategy.selection_policy.get("constraints", {})

    max_false_assignment = float(constraints.get("max_false_assignment_rate", 1.0))
    max_review = float(constraints.get("max_review_rate", 1.0))

    if metrics["false_assignment_rate"] > max_false_assignment:
        raise SystemExit(
            "false_assignment_rate regression: "
            f"{metrics['false_assignment_rate']} > {max_false_assignment}"
        )
    if metrics["needs_review_rate"] > max_review:
        raise SystemExit(
            f"needs_review_rate regression: {metrics['needs_review_rate']} > {max_review}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check eval report against regression constraints."
    )
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    report = args.report or workspace_report_path(
        workspace,
        "latest.json",
        Path("evals/reports/latest.json"),
    )
    check_regression(report, workspace=workspace)


if __name__ == "__main__":
    main()
