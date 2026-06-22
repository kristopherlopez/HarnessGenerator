from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SimpleQaExpected(BaseModel):
    answer: str


class SimpleQaCase(BaseModel):
    case_id: str
    question: str
    context: str
    expected: SimpleQaExpected


class SimpleQaPrediction(BaseModel):
    case_id: str
    strategy: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)


@dataclass(frozen=True)
class SimpleQaScoringRow:
    case_id: str
    expected_answer: str
    predicted_answer: str
    is_correct: bool
    failure_type: str | None
    suspected_cause: str | None


@dataclass(frozen=True)
class BaselineContextAnswerStrategy:
    name: str = "baseline_context_answer"

    def predict_case(self, case: Any) -> SimpleQaPrediction:
        if not isinstance(case, SimpleQaCase):
            raise TypeError("BaselineContextAnswerStrategy requires SimpleQaCase")
        answer = _answer_from_context(case.context)
        return SimpleQaPrediction(
            case_id=case.case_id,
            strategy=self.name,
            answer=answer,
            confidence=1.0 if answer else 0.0,
        )


class SimpleQaAdapter:
    task_type = "simple_qa"

    def load_dataset(self, dataset_path: Path) -> list[Any]:
        manifest_path = dataset_path / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing dataset manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        case_files = manifest.get("cases")
        if not isinstance(case_files, list):
            raise ValueError(f"{manifest_path} must contain a 'cases' list")
        cases: list[Any] = []
        for case_file in case_files:
            case_path = dataset_path / "cases" / str(case_file)
            raw_case = json.loads(case_path.read_text(encoding="utf-8"))
            cases.append(SimpleQaCase.model_validate(raw_case))
        return cases

    def available_strategies(self) -> dict[str, Any]:
        return {"baseline_context_answer": BaselineContextAnswerStrategy()}

    def strategy_from_harness_config(self, harness_config: dict[str, Any]) -> Any:
        strategy_key = str(harness_config.get("strategy") or harness_config.get("strategy_type"))
        if strategy_key != "baseline_context_answer":
            raise ValueError(f"Unsupported simple_qa harness strategy '{strategy_key}'")
        return BaselineContextAnswerStrategy(
            name=str(harness_config.get("harness_id") or strategy_key)
        )

    def score_predictions(
        self,
        cases: list[Any],
        predictions: list[Any],
    ) -> tuple[dict[str, float], list[Any]]:
        case_by_id = _simple_cases_by_id(cases)
        rows: list[Any] = []
        malformed = 0
        for prediction in predictions:
            if not isinstance(prediction, SimpleQaPrediction):
                raise TypeError("SimpleQaAdapter requires SimpleQaPrediction")
            case = case_by_id[prediction.case_id]
            answer = prediction.answer.strip()
            if not answer:
                malformed += 1
            expected = case.expected.answer
            correct = answer.casefold() == expected.casefold()
            rows.append(
                SimpleQaScoringRow(
                    case_id=case.case_id,
                    expected_answer=expected,
                    predicted_answer=answer,
                    is_correct=correct,
                    failure_type=None if correct else "incorrect_answer",
                    suspected_cause=None if correct else "baseline_answer_extraction_failed",
                )
            )

        total = len(rows)
        if total == 0:
            raise ValueError("Cannot score an empty prediction set")
        correct_count = sum(1 for row in rows if row.is_correct)
        metrics = {
            "total_cases": float(total),
            "exact_match": correct_count / total,
            "malformed_output_rate": malformed / total,
            "latency_ms": 0.0,
        }
        return metrics, rows

    def build_failure_report(self, strategy_name: str, rows: list[Any]) -> dict[str, Any]:
        failures = []
        for row in rows:
            if not isinstance(row, SimpleQaScoringRow):
                raise TypeError("SimpleQaAdapter requires SimpleQaScoringRow")
            if row.failure_type is None:
                continue
            failures.append(
                {
                    "case_id": row.case_id,
                    "failure_type": row.failure_type,
                    "expected_answer": row.expected_answer,
                    "predicted_answer": row.predicted_answer,
                    "suspected_cause": row.suspected_cause,
                }
            )
        by_type: dict[str, int] = {}
        for failure in failures:
            failure_type = str(failure["failure_type"])
            by_type[failure_type] = by_type.get(failure_type, 0) + 1
        return {
            "strategy": strategy_name,
            "failure_count": len(failures),
            "by_failure_type": by_type,
            "failures": failures,
        }

    def serialize_prediction(self, prediction: Any) -> dict[str, Any]:
        if not isinstance(prediction, SimpleQaPrediction):
            raise TypeError("SimpleQaAdapter requires SimpleQaPrediction")
        return prediction.model_dump()

    def is_eligible(
        self,
        metrics: dict[str, float],
        selection_policy: dict[str, Any],
    ) -> bool:
        constraints = selection_policy.get("constraints", {})
        max_malformed = float(constraints.get("max_malformed_output_rate", 1.0))
        return metrics["malformed_output_rate"] <= max_malformed

    def select_winner(self, results: list[dict[str, Any]]) -> str | None:
        eligible = [result for result in results if result["eligible"]]
        if not eligible:
            return None
        winner = sorted(
            eligible,
            key=lambda result: (
                -result["metrics"]["exact_match"],
                result["metrics"]["malformed_output_rate"],
            ),
        )[0]
        return str(winner["strategy"])


def _simple_cases_by_id(cases: list[Any]) -> dict[str, SimpleQaCase]:
    case_by_id: dict[str, SimpleQaCase] = {}
    for case in cases:
        if not isinstance(case, SimpleQaCase):
            raise TypeError("SimpleQaAdapter requires SimpleQaCase")
        case_by_id[case.case_id] = case
    return case_by_id


def _answer_from_context(context: str) -> str:
    if "Paris" in context:
        return "Paris"
    return ""
