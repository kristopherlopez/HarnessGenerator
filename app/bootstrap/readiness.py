from __future__ import annotations

import argparse
from pathlib import Path

from app.bootstrap.contracts import load_bootstrap_contracts, write_bootstrap_readiness_report
from app.workspaces import resolve_workspace, workspace_report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate bootstrap contracts.")
    parser.add_argument("--bootstrap-dir", default="bootstrap", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    output = args.output or workspace_report_path(
        workspace,
        "bootstrap_readiness.json",
        Path("evals/reports/bootstrap_readiness.json"),
    )
    contracts = load_bootstrap_contracts(args.bootstrap_dir, workspace=workspace)
    write_bootstrap_readiness_report(contracts, output)


if __name__ == "__main__":
    main()
