from __future__ import annotations

import json
from pathlib import Path

from app.identity.models import EvalCase
from evals.dataset import load_dataset
from evals.run_eval import run_eval

DATASET = Path("workspaces/youtube_speaker_attribution/datasets/small_gold")


def test_load_small_gold_dataset() -> None:
    cases = load_dataset(DATASET)

    assert len(cases) == 10
    assert all(case.segments for case in cases)


def test_run_eval_writes_report(tmp_path: Path) -> None:
    report_path = tmp_path / "latest.json"
    failure_report_path = tmp_path / "latest_failures.json"
    report = run_eval(
        DATASET,
        "review_heavy_low_false_assignment",
        report_path=report_path,
        failure_report_path=failure_report_path,
    )

    assert report["metrics"]["false_assignment_rate"] == 0.0
    assert report["metrics"]["identity_accuracy"] > 0.5
    assert report_path.exists()
    assert failure_report_path.exists()


def test_gold_template_shape_can_validate() -> None:
    template = json.loads(
        Path(
            "workspaces/youtube_speaker_attribution/datasets/small_gold/gold_case_template.json"
        ).read_text(encoding="utf-8")
    )
    case = EvalCase.model_validate(template)

    assert case.media_uri == "media/youtube_REPLACE_ME.mp4"
    assert case.media_type == "video"
    assert case.source is not None
    assert case.annotation is not None
