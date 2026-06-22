from __future__ import annotations

from pathlib import Path

from app.adapters import resolve_task_adapter
from app.harness import build_strategy_hypothesis, execute_strategy_case, summarize_run_results


def test_harness_run_result_keeps_task_input_separate_from_prediction() -> None:
    workspace = Path("workspaces/youtube_speaker_attribution")
    dataset = workspace / "datasets" / "small_gold"
    adapter = resolve_task_adapter(workspace)
    strategy = adapter.available_strategies()["review_heavy_low_false_assignment"]
    case = adapter.load_dataset(dataset)[0]
    hypothesis = build_strategy_hypothesis(
        adapter=adapter,
        strategy_name=strategy.name,
        workspace=workspace,
    )

    execution = execute_strategy_case(
        adapter=adapter,
        strategy=strategy,
        case=case,
        hypothesis=hypothesis,
        dataset=dataset,
        workspace=workspace,
    )

    result = execution.run_result
    assert result.request.harness_id == (
        "youtube_speaker_attribution:review_heavy_low_false_assignment"
    )
    assert result.predicted_task_output["case_id"] == case.case_id
    assert "segments" not in result.request.task_input
    assert "annotation" not in result.request.task_input
    assert "true_person_id" not in str(result.request.task_input)
    assert result.model_calls == []
    assert result.tool_calls == []


def test_simple_workspace_runs_through_same_harness_api() -> None:
    workspace = Path("tests/fixtures/workspaces/simple_qa")
    dataset = workspace / "datasets" / "tiny"
    adapter = resolve_task_adapter(workspace)
    strategy = adapter.available_strategies()["baseline_context_answer"]
    case = adapter.load_dataset(dataset)[0]
    hypothesis = build_strategy_hypothesis(
        adapter=adapter,
        strategy_name=strategy.name,
        workspace=workspace,
    )

    execution = execute_strategy_case(
        adapter=adapter,
        strategy=strategy,
        case=case,
        hypothesis=hypothesis,
        dataset=dataset,
        workspace=workspace,
    )
    summary = summarize_run_results([execution.run_result])

    assert execution.run_result.request.task_type == "simple_qa"
    assert execution.run_result.predicted_task_output["answer"] == "Paris"
    assert "expected" not in execution.run_result.request.task_input
    assert summary["run_count"] == 1
    assert summary["model_call_count"] == 0
