from __future__ import annotations

from pathlib import Path

from app.workspaces.history import _filter_status_lines


def test_git_status_filter_ignores_history_output_under_repo() -> None:
    root = Path.cwd()
    history_path = (
        root
        / "workspaces"
        / "youtube_speaker_attribution"
        / "experiments"
        / "harness_history.jsonl"
    )
    status_lines = [
        " M evals/run_eval.py",
        "?? workspaces/youtube_speaker_attribution/experiments/harness_history.jsonl",
        "?? app/workspaces/history.py",
    ]

    assert _filter_status_lines(root, status_lines, [history_path]) == [
        " M evals/run_eval.py",
        "?? app/workspaces/history.py",
    ]
