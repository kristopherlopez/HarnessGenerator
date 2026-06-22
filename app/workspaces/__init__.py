from __future__ import annotations

from pathlib import Path

DEFAULT_WORKSPACE = Path("workspaces/youtube_speaker_attribution")


def resolve_workspace(workspace: Path | str | None) -> Path | None:
    if workspace is None:
        return None
    return Path(workspace)


def resolve_dataset_path(workspace: Path | None, dataset: Path | str) -> Path:
    dataset_path = Path(dataset)
    if dataset_path.exists():
        return dataset_path
    if workspace is not None:
        workspace_dataset = workspace / "datasets" / str(dataset)
        if workspace_dataset.exists():
            return workspace_dataset
    return dataset_path


def workspace_report_path(workspace: Path | None, filename: str, fallback: Path) -> Path:
    if workspace is None:
        return fallback
    return workspace / "reports" / filename


def workspace_codex_task_path(workspace: Path | None, *parts: str, fallback: Path) -> Path:
    if workspace is None:
        return fallback
    return workspace / "codex_tasks" / Path(*parts)


def workspace_experiment_path(workspace: Path | None, *parts: str, fallback: Path) -> Path:
    if workspace is None:
        return fallback
    return workspace / "experiments" / Path(*parts)


def resolve_harness_path(workspace: Path | None, harness: Path | str | None) -> Path | None:
    if harness is None:
        return None
    path = Path(harness)
    if path.exists():
        return path
    if workspace is None:
        return path

    harness_name = str(harness)
    candidates = [
        workspace / path,
        workspace / "harnesses" / harness_name / "harness.yaml",
        workspace / "experiments" / "generated_harnesses" / harness_name / "harness.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return path
