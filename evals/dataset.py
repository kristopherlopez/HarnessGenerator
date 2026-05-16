from __future__ import annotations

import json
from pathlib import Path

from app.identity.models import EvalCase


def load_dataset(dataset_path: Path | str) -> list[EvalCase]:
    root = Path(dataset_path)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing dataset manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_files = manifest.get("cases")
    if not isinstance(case_files, list):
        raise ValueError(f"{manifest_path} must contain a 'cases' list")

    cases: list[EvalCase] = []
    for case_file in case_files:
        case_path = root / "cases" / str(case_file)
        raw_case = json.loads(case_path.read_text(encoding="utf-8"))
        cases.append(EvalCase.model_validate(raw_case))
    return cases

