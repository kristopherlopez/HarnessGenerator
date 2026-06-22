from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml
from pydantic import BaseModel

from app.adapters import HarnessStrategy, TaskAdapter
from app.harness.models import HarnessHypothesis, HarnessRunRequest, HarnessRunResult, TraceEvent

_HIDDEN_INPUT_KEYS = {
    "annotation",
    "expected",
    "segments",
    "true_display_name",
    "true_person_id",
}


@dataclass(frozen=True)
class HarnessCaseExecution:
    prediction: Any
    run_result: HarnessRunResult


def build_strategy_hypothesis(
    *,
    adapter: TaskAdapter,
    strategy_name: str,
    workspace: Path | None = None,
    harness_id: str | None = None,
    version: str = "registered-strategy-v1",
    declared_change_surface: str = "registered_strategy",
    config: dict[str, Any] | None = None,
) -> HarnessHypothesis:
    return HarnessHypothesis(
        harness_id=harness_id or f"{adapter.task_type}:{strategy_name}",
        version=version,
        task_type=adapter.task_type,
        contract_versions=_contract_versions(workspace),
        declared_change_surface=declared_change_surface,
        strategy_name=strategy_name,
        tool_policy={"allowed_tools": [], "live_external_api_calls": False},
        decomposition_steps=["load_case", "strategy.predict_case", "serialize_prediction"],
        verification_checks=[
            "output_contract_validation_pending",
            "safety_contract_validation_pending",
            "eval_scoring_after_prediction",
        ],
        retry_policy={"max_retries": 0},
        stopping_rules=["single_pass_strategy_execution"],
        confidence_policy={"source": "strategy_defined"},
        review_policy={"source": "strategy_defined"},
        expected_budget_impact={
            "model_calls": 0,
            "tool_calls": 0,
            "live_external_api_calls": 0,
        },
        config=config or {},
    )


def execute_strategy_case(
    *,
    adapter: TaskAdapter,
    strategy: HarnessStrategy,
    case: Any,
    hypothesis: HarnessHypothesis,
    dataset: Path,
    workspace: Path | None = None,
    run_config: dict[str, Any] | None = None,
    budget_limits: dict[str, Any] | None = None,
    allowed_tools: Sequence[str] = (),
    allowed_providers: Sequence[str] = (),
) -> HarnessCaseExecution:
    case_id = _case_id(case)
    request = HarnessRunRequest(
        workspace_id=_workspace_id(workspace),
        workspace_path=workspace.as_posix() if workspace is not None else None,
        dataset=dataset.as_posix(),
        case_id=case_id,
        task_type=adapter.task_type,
        task_input=_task_input(case),
        task_input_ref=_task_input_ref(dataset, case_id),
        harness_id=hypothesis.harness_id,
        harness_version=hypothesis.version,
        run_config=run_config or {},
        budget_limits=budget_limits or {},
        allowed_tools=list(allowed_tools),
        allowed_providers=list(allowed_providers),
    )
    start = perf_counter()
    trace_events = [
        _trace_event(
            "harness_started",
            "Started registered strategy harness.",
            {"strategy": strategy.name},
        )
    ]
    prediction = strategy.predict_case(case)
    trace_events.append(
        _trace_event(
            "prediction_created",
            "Strategy returned a task prediction.",
            {"strategy": strategy.name},
        )
    )
    predicted_output = adapter.serialize_prediction(prediction)
    trace_events.append(
        _trace_event(
            "prediction_serialized",
            "Prediction was serialized for reporting.",
            {"output_fields": sorted(predicted_output)},
        )
    )
    latency_ms = round((perf_counter() - start) * 1000, 6)
    run_result = HarnessRunResult(
        request=request,
        predicted_task_output=predicted_output,
        trace_events=trace_events,
        latency_ms=latency_ms,
        reproducibility={
            "hypothesis_sha256": _json_hash(hypothesis.model_dump(mode="json")),
            "runner": "registered_strategy_runner",
        },
    )
    return HarnessCaseExecution(prediction=prediction, run_result=run_result)


def summarize_run_results(results: Sequence[HarnessRunResult]) -> dict[str, Any]:
    output_status_counts: dict[str, int] = {}
    safety_status_counts: dict[str, int] = {}
    error_count = 0
    model_call_count = 0
    tool_call_count = 0
    latency_ms = 0.0
    for result in results:
        output_status_counts[result.output_validation_status] = (
            output_status_counts.get(result.output_validation_status, 0) + 1
        )
        safety_status_counts[result.safety_validation_status] = (
            safety_status_counts.get(result.safety_validation_status, 0) + 1
        )
        error_count += len(result.errors)
        model_call_count += len(result.model_calls)
        tool_call_count += len(result.tool_calls)
        latency_ms += result.latency_ms
    return {
        "run_count": len(results),
        "output_validation_status": output_status_counts,
        "safety_validation_status": safety_status_counts,
        "error_count": error_count,
        "model_call_count": model_call_count,
        "tool_call_count": tool_call_count,
        "latency_ms": round(latency_ms, 6),
    }


def _case_id(case: Any) -> str | None:
    raw_case_id = getattr(case, "case_id", None)
    return str(raw_case_id) if raw_case_id is not None else None


def _task_input_ref(dataset: Path, case_id: str | None) -> str | None:
    if case_id is None:
        return None
    return f"{dataset.as_posix()}#{case_id}"


def _task_input(case: Any) -> dict[str, Any]:
    sanitized = _sanitize(case)
    return sanitized if isinstance(sanitized, dict) else {"value": sanitized}


def _sanitize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _sanitize(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
            if str(key) not in _HIDDEN_INPUT_KEYS
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _trace_event(event_type: str, message: str, metadata: dict[str, Any]) -> TraceEvent:
    return TraceEvent(
        event_type=event_type,
        message=message,
        timestamp_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        metadata=metadata,
    )


def _workspace_id(workspace: Path | None) -> str | None:
    manifest = _workspace_manifest(workspace)
    raw_workspace_id = manifest.get("workspace_id")
    return str(raw_workspace_id) if raw_workspace_id is not None else None


def _workspace_manifest(workspace: Path | None) -> dict[str, Any]:
    if workspace is None:
        return {}
    task_path = workspace / "task.yaml"
    if not task_path.exists():
        return {}
    loaded = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _contract_versions(workspace: Path | None) -> dict[str, str]:
    if workspace is None:
        return {}
    versions: dict[str, str] = {}
    for path in sorted((workspace / "contracts").glob("*.yaml")):
        versions[f"contracts/{path.name}"] = _file_hash(path)
    task_path = workspace / "task.yaml"
    if task_path.exists():
        versions["task.yaml"] = _file_hash(task_path)
    return versions


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
