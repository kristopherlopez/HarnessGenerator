from __future__ import annotations

from pathlib import Path

from evals.compare_strategies import compare_strategies

WORKSPACE = Path("workspaces/youtube_speaker_attribution")


def test_strategy_comparison_rejects_risky_high_accuracy_strategy(tmp_path: Path) -> None:
    report = compare_strategies(
        WORKSPACE / "datasets" / "small_gold",
        workspace=WORKSPACE,
        output_path=tmp_path / "strategy_comparison.json",
    )
    result_by_strategy = {result["strategy"]: result for result in report["results"]}

    assert result_by_strategy["risky_top_candidate"]["eligible"] is False
    assert report["winner"] == "review_heavy_low_false_assignment"
