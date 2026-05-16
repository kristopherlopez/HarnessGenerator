from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

REQUIRED_CONTRACT_FILES = {
    "domain": "domain_contract.yaml",
    "input": "input_contract.yaml",
    "output": "output_contract.yaml",
    "tools": "tool_registry.yaml",
    "strategy": "strategy_space.yaml",
    "harness_search": "harness_search_space.yaml",
    "metrics": "metric_contract.yaml",
    "safety": "safety_contract.yaml",
    "datasets": "dataset_manifest.yaml",
    "codex_task": "codex_task_policy.yaml",
}


class DomainContract(BaseModel):
    domain: str
    goal: dict[str, bool]
    population: dict[str, Any]
    identity_policy: dict[str, bool]
    primary_risk: str
    secondary_risks: list[str]


class FieldListContract(BaseModel):
    required_fields: list[str] = Field(min_length=1)


class OutputContract(BaseModel):
    transcript_segment: FieldListContract
    resolution_status: dict[str, list[str]]
    speaker: FieldListContract
    evidence_summary: FieldListContract
    review: FieldListContract

    @field_validator("resolution_status")
    @classmethod
    def validate_resolution_status(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        allowed = set(value.get("allowed_values", []))
        required = {"resolved", "unknown", "needs_review"}
        missing = required - allowed
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"resolution_status is missing allowed values: {missing_text}")
        return value


class Metric(BaseModel):
    name: str
    lower_is_better: bool


class MetricContract(BaseModel):
    primary_metric: Metric
    secondary_metrics: list[Metric]
    selection_rules: dict[str, list[str]]


class StrategySpaceContract(BaseModel):
    candidate_generation: list[str]
    resolution_strategies: list[str]
    threshold_search: dict[str, Any]
    selection_policy: dict[str, Any]


class HarnessSearchSpaceContract(BaseModel):
    change_surfaces: dict[str, list[str]]
    staged_unlocks: dict[str, list[str]]
    prohibited_changes_without_explicit_task: list[str]
    candidate_requirements: list[str]


class CodexTaskPolicy(BaseModel):
    generated_task_must_include: list[str]
    generated_task_must_not: list[str]


class BootstrapContracts(BaseModel):
    root: Path
    raw: dict[str, dict[str, Any]]
    domain: DomainContract
    output: OutputContract
    metrics: MetricContract
    strategy: StrategySpaceContract
    harness_search: HarnessSearchSpaceContract
    codex_task: CodexTaskPolicy


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return loaded


def load_bootstrap_contracts(
    root: Path | str = "bootstrap",
    workspace: Path | str | None = None,
) -> BootstrapContracts:
    contract_root = Path(root)
    raw: dict[str, dict[str, Any]] = {}

    for contract_name, filename in REQUIRED_CONTRACT_FILES.items():
        path = contract_root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required contract: {path}")
        raw[contract_name] = _read_yaml(path)

    if workspace is not None:
        workspace_contract_root = Path(workspace) / "contracts"
        if workspace_contract_root.exists():
            for contract_name, filename in REQUIRED_CONTRACT_FILES.items():
                path = workspace_contract_root / filename
                if path.exists():
                    raw[contract_name] = _read_yaml(path)

    try:
        return BootstrapContracts(
            root=contract_root,
            raw=raw,
            domain=DomainContract.model_validate(raw["domain"]),
            output=OutputContract.model_validate(raw["output"]),
            metrics=MetricContract.model_validate(raw["metrics"]),
            strategy=StrategySpaceContract.model_validate(raw["strategy"]),
            harness_search=HarnessSearchSpaceContract.model_validate(raw["harness_search"]),
            codex_task=CodexTaskPolicy.model_validate(raw["codex_task"]),
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid bootstrap contract: {exc}") from exc


def write_bootstrap_readiness_report(
    contracts: BootstrapContracts,
    output_path: Path | str = "evals/reports/bootstrap_readiness.json",
) -> Path:
    import json

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "ready",
        "contracts_loaded": sorted(REQUIRED_CONTRACT_FILES.values()),
        "domain": contracts.domain.domain,
        "primary_metric": contracts.metrics.primary_metric.name,
        "resolution_strategies": contracts.strategy.resolution_strategies,
        "harness_change_surfaces": sorted(contracts.harness_search.change_surfaces),
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
