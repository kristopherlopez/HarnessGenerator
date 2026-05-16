from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evals.metrics import SegmentScoringRow


def write_json(path: Path | str, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def build_failure_report(strategy: str, rows: list[SegmentScoringRow]) -> dict[str, Any]:
    failures = [
        {
            "case_id": row.case_id,
            "segment_id": row.segment_id,
            "failure_type": row.failure_type,
            "true_person_id": row.true_person_id,
            "predicted_person_id": row.predicted_person_id,
            "resolution_status": row.resolution_status,
            "condition": row.condition,
            "suspected_cause": _suspected_cause(row.failure_type),
        }
        for row in rows
        if row.failure_type is not None
    ]
    by_type: dict[str, int] = {}
    for failure in failures:
        failure_type = str(failure["failure_type"])
        by_type[failure_type] = by_type.get(failure_type, 0) + 1

    return {
        "strategy": strategy,
        "failure_count": len(failures),
        "by_failure_type": by_type,
        "failures": failures,
    }


def _suspected_cause(failure_type: str | None) -> str:
    if failure_type == "false_assignment":
        return "resolver accepted weak or conflicting identity evidence"
    if failure_type == "missed_known_identity":
        return "strategy was too conservative or lacked sufficient evidence"
    if failure_type == "unknown_forced_to_known":
        return "open-set unknown handling failed"
    return "unknown"

