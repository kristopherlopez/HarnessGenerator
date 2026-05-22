from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel

from app.bootstrap.contracts import load_bootstrap_contracts
from app.workspaces import resolve_dataset_path, resolve_workspace, workspace_report_path

CheckStatus = Literal["pass", "fail"]
ReadinessStatus = Literal["optimization_ready", "not_ready"]


class ReadinessCheck(BaseModel):
    name: str
    status: CheckStatus
    message: str


class WorkspaceReadinessReport(BaseModel):
    workspace: str
    status: ReadinessStatus
    checks: list[ReadinessCheck]

    @property
    def ready(self) -> bool:
        return self.status == "optimization_ready"


def validate_workspace_readiness(
    workspace: Path | str,
    output_path: Path | None = None,
) -> WorkspaceReadinessReport:
    workspace_path = Path(workspace)
    checks: list[ReadinessCheck] = []

    task_manifest = _load_task_manifest(workspace_path, checks)
    contracts = _load_contracts(workspace_path, checks)

    if task_manifest is not None:
        paths = task_manifest.get("paths")
        if isinstance(paths, dict):
            _check_declared_paths(workspace_path, paths, checks)
        else:
            checks.append(_fail("task_paths", "task.yaml must contain a paths object"))

        default_dataset = task_manifest.get("default_dataset")
        _check_default_dataset(workspace_path, default_dataset, checks)

        default_strategy = task_manifest.get("default_strategy") or task_manifest.get(
            "default_harness"
        )
        _check_default_strategy(default_strategy, contracts, checks)

        reports_path = (
            _declared_path(workspace_path, paths, "reports")
            if isinstance(paths, dict)
            else None
        )
        _check_reports_writable(reports_path, checks)

    status: ReadinessStatus = (
        "optimization_ready" if all(check.status == "pass" for check in checks) else "not_ready"
    )
    report = WorkspaceReadinessReport(
        workspace=str(workspace_path),
        status=status,
        checks=checks,
    )
    _write_readiness_report(report, output_path or workspace_report_path(
        workspace_path,
        "workspace_readiness.json",
        Path("evals/reports/workspace_readiness.json"),
    ))
    return report


def _load_task_manifest(
    workspace: Path,
    checks: list[ReadinessCheck],
) -> dict[str, Any] | None:
    task_path = workspace / "task.yaml"
    if not task_path.exists():
        checks.append(_fail("task_manifest", f"Missing workspace manifest: {task_path}"))
        return None

    loaded = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        checks.append(_fail("task_manifest", f"{task_path} must contain a YAML object"))
        return None

    required_fields = ["workspace_id", "default_dataset", "paths"]
    missing = [field for field in required_fields if not loaded.get(field)]
    if missing:
        checks.append(
            _fail("task_manifest", f"task.yaml is missing required fields: {', '.join(missing)}")
        )
        return loaded

    if not (loaded.get("default_strategy") or loaded.get("default_harness")):
        checks.append(
            _fail("task_manifest", "task.yaml must declare default_strategy or default_harness")
        )
        return loaded

    checks.append(_pass("task_manifest", f"Loaded workspace manifest: {task_path}"))
    return loaded


def _load_contracts(workspace: Path, checks: list[ReadinessCheck]) -> Any | None:
    contract_path = workspace / "contracts"
    if not contract_path.exists():
        checks.append(_fail("contracts", f"Missing workspace contracts directory: {contract_path}"))
        return None

    try:
        contracts = load_bootstrap_contracts(workspace=workspace)
    except (FileNotFoundError, ValueError) as exc:
        checks.append(_fail("contracts", f"Contract validation failed: {exc}"))
        return None

    checks.append(_pass("contracts", "Merged bootstrap and workspace contracts loaded"))
    return contracts


def _check_declared_paths(
    workspace: Path,
    paths: dict[Any, Any],
    checks: list[ReadinessCheck],
) -> None:
    missing: list[str] = []
    for key, value in paths.items():
        path = workspace / str(value)
        if not path.exists():
            missing.append(f"{key}={path}")
    if missing:
        checks.append(_fail("declared_paths", f"Missing declared paths: {', '.join(missing)}"))
        return
    checks.append(_pass("declared_paths", "All task.yaml paths exist"))


def _check_default_dataset(
    workspace: Path,
    default_dataset: Any,
    checks: list[ReadinessCheck],
) -> None:
    if not default_dataset:
        checks.append(_fail("default_dataset", "task.yaml must declare default_dataset"))
        return

    dataset_path = resolve_dataset_path(workspace, str(default_dataset))
    if not dataset_path.exists():
        checks.append(_fail("default_dataset", f"Default dataset is missing: {dataset_path}"))
        return

    manifest_path = dataset_path / "manifest.json"
    if not manifest_path.exists():
        checks.append(
            _fail("default_dataset", f"Default dataset manifest is missing: {manifest_path}")
        )
        return

    checks.append(_pass("default_dataset", f"Default dataset exists: {dataset_path}"))


def _check_default_strategy(
    default_strategy: Any,
    contracts: Any | None,
    checks: list[ReadinessCheck],
) -> None:
    if not default_strategy:
        checks.append(
            _fail("default_strategy", "task.yaml must declare default_strategy or default_harness")
        )
        return

    if contracts is None:
        checks.append(
            _fail("default_strategy", "Cannot validate default strategy without valid contracts")
        )
        return

    configured = set(contracts.strategy.resolution_strategies)
    if str(default_strategy) not in configured:
        checks.append(
            _fail(
                "default_strategy",
                f"Default strategy '{default_strategy}' is not listed in strategy_space.yaml",
            )
        )
        return

    checks.append(_pass("default_strategy", f"Default strategy is declared: {default_strategy}"))


def _check_reports_writable(
    reports_path: Path | None,
    checks: list[ReadinessCheck],
) -> None:
    if reports_path is None:
        checks.append(_fail("reports_writable", "Cannot locate declared reports path"))
        return
    if not reports_path.exists():
        checks.append(_fail("reports_writable", f"Reports path is missing: {reports_path}"))
        return

    probe = reports_path / ".readiness_write_check"
    try:
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        checks.append(_fail("reports_writable", f"Reports path is not writable: {exc}"))
        return

    checks.append(_pass("reports_writable", f"Reports path is writable: {reports_path}"))


def _declared_path(workspace: Path, paths: dict[Any, Any], key: str) -> Path | None:
    value = paths.get(key)
    if value is None:
        return None
    return workspace / str(value)


def _write_readiness_report(report: WorkspaceReadinessReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.model_dump(), indent=2) + "\n", encoding="utf-8")
    return output_path


def _pass(name: str, message: str) -> ReadinessCheck:
    return ReadinessCheck(name=name, status="pass", message=message)


def _fail(name: str, message: str) -> ReadinessCheck:
    return ReadinessCheck(name=name, status="fail", message=message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate workspace readiness.")
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise SystemExit("--workspace is required")

    report = validate_workspace_readiness(workspace, output_path=args.output)
    print(json.dumps(report.model_dump(), indent=2))
    if not report.ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
