from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from app.identity.strategies import available_strategies
from evals.dataset import load_dataset
from evals.metrics import score_predictions
from evals.reports import build_failure_report


class YouTubeSpeakerAttributionAdapter:
    task_type = "youtube_speaker_attribution"

    def load_dataset(self, dataset_path: Path) -> list[Any]:
        return load_dataset(dataset_path)

    def available_strategies(self) -> dict[str, Any]:
        return available_strategies()

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
