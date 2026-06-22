from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from app.identity.strategies import (
    BaselineUnknownStrategy,
    ConservativeEvidenceStrategy,
    RiskyTopCandidateStrategy,
    available_strategies,
)
from evals.dataset import load_dataset
from evals.metrics import score_predictions
from evals.reports import build_failure_report


class YouTubeSpeakerAttributionAdapter:
    task_type = "youtube_speaker_attribution"

    def load_dataset(self, dataset_path: Path) -> list[Any]:
        return load_dataset(dataset_path)

    def available_strategies(self) -> dict[str, Any]:
        return available_strategies()

    def strategy_from_harness_config(self, harness_config: dict[str, Any]) -> Any:
        strategy_key = str(
            harness_config.get("strategy_type")
            or harness_config.get("strategy")
            or harness_config.get("harness_id")
        )
        harness_id = str(harness_config.get("harness_id") or strategy_key)
        if strategy_key == "baseline_unknown":
            return BaselineUnknownStrategy(name=harness_id)
        if strategy_key == "risky_top_candidate":
            return RiskyTopCandidateStrategy(name=harness_id)
        if strategy_key in {"review_heavy_low_false_assignment", "conservative_evidence"}:
            resolver_config = harness_config.get("resolver_config", {})
            if not isinstance(resolver_config, dict):
                raise ValueError("resolver_config must be a mapping")
            return ConservativeEvidenceStrategy(
                name=harness_id,
                **_conservative_resolver_params(resolver_config),
            )
        raise ValueError(f"Unsupported YouTube harness strategy '{strategy_key}'")

    def score_predictions(
        self,
        cases: list[Any],
        predictions: list[Any],
    ) -> tuple[dict[str, float], list[Any]]:
        return score_predictions(cases, predictions)

    def build_failure_report(self, strategy_name: str, rows: list[Any]) -> dict[str, Any]:
        return build_failure_report(strategy_name, rows)

    def serialize_prediction(self, prediction: Any) -> dict[str, Any]:
        return cast(dict[str, Any], prediction.model_dump())

    def is_eligible(
        self,
        metrics: dict[str, float],
        selection_policy: dict[str, Any],
    ) -> bool:
        constraints = selection_policy.get("constraints", {})
        max_false_assignment = float(constraints.get("max_false_assignment_rate", 1.0))
        max_review = float(constraints.get("max_review_rate", 1.0))
        return (
            metrics["false_assignment_rate"] <= max_false_assignment
            and metrics["needs_review_rate"] <= max_review
        )

    def select_winner(self, results: list[dict[str, Any]]) -> str | None:
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


def _conservative_resolver_params(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "assignment_threshold",
        "voice_only_assignment_threshold",
        "review_threshold",
        "max_review_rate",
        "minimum_review_slots",
        "overlap_handling_policy",
        "margin_threshold",
        "voice_only_margin_threshold",
        "min_voice_duration_seconds",
        "min_voice_only_duration_seconds",
        "high_overlap_levels",
    }
    params = {key: value for key, value in config.items() if key in allowed}
    if "high_overlap_levels" in params:
        raw_levels = params["high_overlap_levels"]
        if not isinstance(raw_levels, list):
            raise ValueError("high_overlap_levels must be a list")
        params["high_overlap_levels"] = tuple(str(level) for level in raw_levels)
    return params
