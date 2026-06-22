from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ValidationStatus = Literal["passed", "failed", "not_validated"]
OptimizerAction = Literal["accept", "reject", "revise", "generate_task"]


class TraceEvent(BaseModel):
    event_type: str
    message: str
    timestamp_utc: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCallRecord(BaseModel):
    provider: str
    model: str
    purpose: str
    input_sha256: str | None = None
    output_sha256: str | None = None
    cached: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None


class ToolCallRecord(BaseModel):
    tool_name: str
    purpose: str
    input_sha256: str | None = None
    output_sha256: str | None = None
    cached: bool = False
    latency_ms: float | None = None
    error: str | None = None


class HarnessHypothesis(BaseModel):
    schema_version: int = 1
    harness_id: str
    version: str
    task_type: str
    contract_versions: dict[str, str] = Field(default_factory=dict)
    declared_change_surface: str
    strategy_name: str | None = None
    prompts: list[dict[str, Any]] = Field(default_factory=list)
    model_provider_routing: list[dict[str, Any]] = Field(default_factory=list)
    tool_policy: dict[str, Any] = Field(default_factory=dict)
    decomposition_steps: list[str] = Field(default_factory=list)
    verification_checks: list[str] = Field(default_factory=list)
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    stopping_rules: list[str] = Field(default_factory=list)
    confidence_policy: dict[str, Any] = Field(default_factory=dict)
    review_policy: dict[str, Any] = Field(default_factory=dict)
    expected_budget_impact: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


class HarnessRunRequest(BaseModel):
    schema_version: int = 1
    workspace_id: str | None = None
    workspace_path: str | None = None
    dataset: str
    case_id: str | None = None
    task_type: str
    task_input: dict[str, Any] = Field(default_factory=dict)
    task_input_ref: str | None = None
    harness_id: str
    harness_version: str
    run_config: dict[str, Any] = Field(default_factory=dict)
    budget_limits: dict[str, Any] = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_providers: list[str] = Field(default_factory=list)


class HarnessRunResult(BaseModel):
    schema_version: int = 1
    request: HarnessRunRequest
    predicted_task_output: dict[str, Any]
    output_validation_status: ValidationStatus = "not_validated"
    safety_validation_status: ValidationStatus = "not_validated"
    trace_events: list[TraceEvent] = Field(default_factory=list)
    model_calls: list[ModelCallRecord] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    retries: int = 0
    errors: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    cost: dict[str, Any] = Field(default_factory=dict)
    reproducibility: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    schema_version: int = 1
    dataset: str
    task_type: str
    harness_id: str
    metrics: dict[str, float]
    failure_count: int = 0
    failure_categories: dict[str, int] = Field(default_factory=dict)
    constraint_violations: list[str] = Field(default_factory=list)
    scorer_version: str | None = None
    report_path: str | None = None


class OptimizerDecision(BaseModel):
    schema_version: int = 1
    action: OptimizerAction
    rationale: str
    target_failure_types: list[str] = Field(default_factory=list)
    proposed_change_surface: str | None = None
    next_harness_hypothesis: HarnessHypothesis | None = None
    codex_task_path: str | None = None
    risk_notes: list[str] = Field(default_factory=list)
