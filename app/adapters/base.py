from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class HarnessStrategy(Protocol):
    name: str

    def predict_case(self, case: Any) -> Any:
        """Run the strategy for one task case."""


class TaskAdapter(Protocol):
    task_type: str

    def load_dataset(self, dataset_path: Path) -> list[Any]:
        """Load a dataset split or fixture into task-specific case objects."""

    def available_strategies(self) -> dict[str, HarnessStrategy]:
        """Return runnable strategies for this task family."""

    def score_predictions(
        self,
        cases: list[Any],
        predictions: list[Any],
    ) -> tuple[dict[str, float], list[Any]]:
        """Score task-specific predictions and return metrics plus failure-mining rows."""

    def build_failure_report(self, strategy_name: str, rows: list[Any]) -> dict[str, Any]:
        """Build a task-specific failure report from scoring rows."""

    def serialize_prediction(self, prediction: Any) -> dict[str, Any]:
        """Convert a task-specific prediction object into report JSON."""

    def is_eligible(
        self,
        metrics: dict[str, float],
        selection_policy: dict[str, Any],
    ) -> bool:
        """Return whether metrics satisfy task-specific winner constraints."""

    def select_winner(self, results: list[dict[str, Any]]) -> str | None:
        """Choose the best eligible strategy from comparison results."""
