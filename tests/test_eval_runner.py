from __future__ import annotations

import json
from pathlib import Path

from app.identity.models import EvalCase
from evals.dataset import load_dataset
from evals.run_eval import run_eval

DATASET = Path("workspaces/youtube_speaker_attribution/datasets/small_gold")


def test_load_small_gold_dataset() -> None:
    cases = load_dataset(DATASET)

    assert len(cases) == 12
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
    assert report["harness_hypothesis"]["harness_id"] == (
        "youtube_speaker_attribution:review_heavy_low_false_assignment"
    )
    assert report["harness_run_summary"]["run_count"] == 12
    assert report["harness_run_results"][0]["request"]["task_input"]
    assert "segments" not in report["harness_run_results"][0]["request"]["task_input"]
    assert report_path.exists()
    assert failure_report_path.exists()

    failure_report = json.loads(failure_report_path.read_text(encoding="utf-8"))
    similar_voice_failure = next(
        failure
        for failure in failure_report["failures"]
        if failure["case_id"] == "similar_voices"
    )
    assert similar_voice_failure["resolution_status"] == "needs_review"
    assert similar_voice_failure["review_reason"] == "ambiguous_voice_candidate_margin"
    assert similar_voice_failure["evidence_conflicts"] == [
        "ambiguous_voice_candidate_margin"
    ]
    assert (
        similar_voice_failure["suspected_cause"]
        == "voice candidates were close; human review required"
    )


def test_run_eval_can_append_workspace_history(tmp_path: Path) -> None:
    report_path = tmp_path / "latest.json"
    failure_report_path = tmp_path / "latest_failures.json"
    history_path = tmp_path / "harness_history.jsonl"

    report = run_eval(
        DATASET,
        "review_heavy_low_false_assignment",
        report_path=report_path,
        failure_report_path=failure_report_path,
        workspace=Path("workspaces/youtube_speaker_attribution"),
        record_history=True,
        history_path=history_path,
    )

    assert report["history_entry_path"] == str(history_path)
    entries = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["loop"] == "evaluate_harness_loop"
    assert entry["run_type"] == "eval"
    assert entry["harness"]["strategy"] == "review_heavy_low_false_assignment"
    assert entry["dataset"]["cases"]
    assert entry["gold"]["cases"] == [
        "youtube_gG1Lq2pIgGM_part_000.json",
        "youtube_gG1Lq2pIgGM_part_001.json",
        "youtube_gG1Lq2pIgGM_part_002.json",
        "youtube_gG1Lq2pIgGM_part_003.json",
    ]
    assert entry["metrics"]["false_assignment_rate"] == 0.0
    assert entry["failures"]["count"] >= 1
    assert entry["harness_hypothesis"]["harness_id"] == (
        "youtube_speaker_attribution:review_heavy_low_false_assignment"
    )
    assert entry["harness_run_summary"]["model_call_count"] == 0


def test_run_eval_can_execute_harness_config(tmp_path: Path) -> None:
    harness_path = tmp_path / "candidate_001" / "harness.yaml"
    harness_path.parent.mkdir(parents=True)
    harness_path.write_text(
        """
schema_version: 0.1
harness_id: candidate_001
workspace_id: youtube_speaker_attribution
status: generated_candidate
strategy: review_heavy_low_false_assignment
strategy_type: conservative_evidence
change_surface: thresholds_and_policies
change_option: assignment_threshold
resolver_config:
  assignment_threshold: 0.85
  voice_only_assignment_threshold: 0.80
  review_threshold: 0.60
  max_review_rate: 0.25
  minimum_review_slots: 1
  overlap_handling_policy: require_corroborating_signal_on_high_overlap
  high_overlap_levels: [high]
  margin_threshold: 0.08
  voice_only_margin_threshold: 0.10
  min_voice_duration_seconds: 2.5
  min_voice_only_duration_seconds: 5.0
""".lstrip(),
        encoding="utf-8",
    )

    report = run_eval(
        DATASET,
        None,
        report_path=tmp_path / "latest.json",
        failure_report_path=tmp_path / "latest_failures.json",
        workspace=Path("workspaces/youtube_speaker_attribution"),
        harness_path=harness_path,
    )

    assert report["strategy"] == "candidate_001"
    assert report["harness_config_path"] == str(harness_path)
    assert report["harness_hypothesis"]["harness_id"] == (
        "youtube_speaker_attribution:candidate_001"
    )
    assert report["harness_run_summary"]["model_call_count"] == 0


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
