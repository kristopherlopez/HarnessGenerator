from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import yaml

DEFAULT_HISTORY_NAME = "harness_history.jsonl"


class Digest(Protocol):
    def update(self, data: bytes, /) -> object: ...


def workspace_history_path(workspace: Path) -> Path:
    return workspace / "experiments" / DEFAULT_HISTORY_NAME


def append_history_entry(
    workspace: Path,
    entry: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    path = output_path or workspace_history_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return path


def build_eval_history_entry(
    *,
    workspace: Path,
    dataset: Path,
    strategy_name: str,
    metrics: dict[str, Any],
    failure_report: dict[str, Any],
    report_path: Path,
    failure_report_path: Path,
    loop_name: str = "evaluate_harness_loop",
    history_output_path: Path | None = None,
    harness_config_path: Path | None = None,
    harness_hypothesis: dict[str, Any] | None = None,
    harness_run_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now(UTC)
    task_manifest = _load_task_manifest(workspace)
    active_artifacts = _dict_or_empty(task_manifest.get("active_artifacts"))
    default_strategy = str(task_manifest.get("default_strategy", strategy_name))
    harness_path = (
        harness_config_path
        or workspace / "harnesses" / default_strategy / "harness.yaml"
    )
    seed_profile_path = _workspace_path(workspace, active_artifacts.get("seed_profile"))
    gold_dataset_name = str(active_artifacts.get("gold_dataset", "seed_gold"))
    review_dataset_name = str(active_artifacts.get("active_review_dataset", "seeded_review_global"))
    gold_manifest_path = workspace / "datasets" / gold_dataset_name / "manifest.json"
    review_manifest_path = workspace / "datasets" / review_dataset_name / "manifest.json"

    return {
        "schema_version": 1,
        "run_id": _run_id(timestamp, loop_name, "eval", strategy_name),
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "loop": loop_name,
        "run_type": "eval",
        "workspace": _workspace_metadata(workspace, task_manifest),
        "git": _git_metadata(
            workspace,
            ignored_paths=[history_output_path or workspace_history_path(workspace)],
        ),
        "dataset": _dataset_metadata(workspace, dataset),
        "gold": {
            "dataset": gold_dataset_name,
            "manifest": _file_metadata(workspace, gold_manifest_path),
            "cases": _manifest_cases(gold_manifest_path),
        },
        "review_queue": {
            "dataset": review_dataset_name,
            "manifest": _file_metadata(workspace, review_manifest_path),
            "cases": _manifest_cases(review_manifest_path),
        },
        "seed_profile": _file_metadata(workspace, seed_profile_path),
        "harness": {
            "strategy": strategy_name,
            "default_strategy": default_strategy,
            "config": _file_metadata(workspace, harness_path),
        },
        "harness_hypothesis": harness_hypothesis,
        "harness_run_summary": harness_run_summary,
        "metrics": metrics,
        "failures": {
            "count": int(failure_report.get("failure_count", 0)),
            "by_failure_type": failure_report.get("by_failure_type", {}),
        },
        "outputs": {
            "eval_report": _relative_to_workspace(workspace, report_path),
            "failure_report": _relative_to_workspace(workspace, failure_report_path),
        },
    }


def build_strategy_comparison_history_entry(
    *,
    workspace: Path,
    dataset: Path,
    report: dict[str, Any],
    output_path: Path,
    loop_name: str = "evaluate_harness_loop",
    history_output_path: Path | None = None,
    harness_hypotheses: dict[str, Any] | None = None,
    harness_run_summaries: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now(UTC)
    task_manifest = _load_task_manifest(workspace)
    active_artifacts = _dict_or_empty(task_manifest.get("active_artifacts"))
    seed_profile_path = _workspace_path(workspace, active_artifacts.get("seed_profile"))
    gold_dataset_name = str(active_artifacts.get("gold_dataset", "seed_gold"))
    review_dataset_name = str(active_artifacts.get("active_review_dataset", "seeded_review_global"))
    gold_manifest_path = workspace / "datasets" / gold_dataset_name / "manifest.json"
    review_manifest_path = workspace / "datasets" / review_dataset_name / "manifest.json"
    winner = str(report.get("winner", "unknown"))
    harness_path = workspace / "harnesses" / winner / "harness.yaml"

    return {
        "schema_version": 1,
        "run_id": _run_id(timestamp, loop_name, "strategy_comparison", winner),
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "loop": loop_name,
        "run_type": "strategy_comparison",
        "workspace": _workspace_metadata(workspace, task_manifest),
        "git": _git_metadata(
            workspace,
            ignored_paths=[history_output_path or workspace_history_path(workspace)],
        ),
        "dataset": _dataset_metadata(workspace, dataset),
        "gold": {
            "dataset": gold_dataset_name,
            "manifest": _file_metadata(workspace, gold_manifest_path),
            "cases": _manifest_cases(gold_manifest_path),
        },
        "review_queue": {
            "dataset": review_dataset_name,
            "manifest": _file_metadata(workspace, review_manifest_path),
            "cases": _manifest_cases(review_manifest_path),
        },
        "seed_profile": _file_metadata(workspace, seed_profile_path),
        "harness": {
            "winner": winner,
            "config": _file_metadata(workspace, harness_path),
        },
        "harness_hypotheses": harness_hypotheses,
        "harness_run_summaries": harness_run_summaries,
        "selection_policy": report.get("selection_policy", {}),
        "strategy_results": [
            {
                "strategy": item.get("strategy"),
                "eligible": item.get("eligible"),
                "metrics": item.get("metrics", {}),
            }
            for item in _list_of_dicts(report.get("results"))
        ],
        "outputs": {
            "strategy_comparison": _relative_to_workspace(workspace, output_path),
        },
    }


def _run_id(
    timestamp: datetime,
    loop_name: str,
    run_type: str,
    suffix: str,
) -> str:
    compact_timestamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    return f"{compact_timestamp}_{_slug(loop_name)}_{_slug(run_type)}_{_slug(suffix)}"


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value).strip("_")


def _load_task_manifest(workspace: Path) -> dict[str, Any]:
    task_path = workspace / "task.yaml"
    if not task_path.exists():
        return {}
    loaded = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _workspace_metadata(workspace: Path, task_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": workspace.as_posix(),
        "workspace_id": task_manifest.get("workspace_id"),
        "task_manifest": _file_metadata(workspace, workspace / "task.yaml"),
    }


def _git_metadata(
    workspace: Path,
    ignored_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    root = _git_root(workspace)
    if root is None:
        return {"sha": None, "dirty": None, "status_short": []}

    sha = _git_output(root, ["rev-parse", "HEAD"])
    status = _git_output(root, ["status", "--short"])
    status_lines = status.splitlines() if status else []
    status_lines = _filter_status_lines(root, status_lines, ignored_paths)
    return {
        "sha": sha or None,
        "dirty": bool(status_lines),
        "status_short": status_lines,
    }


def _filter_status_lines(
    git_root: Path,
    status_lines: list[str],
    ignored_paths: Sequence[Path],
) -> list[str]:
    ignored = _git_relative_paths(git_root, ignored_paths)
    if not ignored:
        return status_lines
    return [
        line
        for line in status_lines
        if _status_path(line) not in ignored
    ]


def _git_relative_paths(git_root: Path, paths: Sequence[Path]) -> set[str]:
    root = git_root.resolve()
    relative_paths: set[str] = set()
    for path in paths:
        try:
            relative_paths.add(path.resolve().relative_to(root).as_posix())
        except ValueError:
            continue
    return relative_paths


def _status_path(status_line: str) -> str:
    path = status_line[3:] if len(status_line) > 3 else status_line
    if " -> " in path:
        return path.split(" -> ", maxsplit=1)[1]
    return path


def _git_root(path: Path) -> Path | None:
    current = path.resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    return None


def _git_output(
    cwd: Path,
    args: list[str],
) -> str | None:
    command = ["git", "-c", f"safe.directory={cwd.as_posix()}", *args]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _dataset_metadata(workspace: Path, dataset: Path) -> dict[str, Any]:
    manifest_path = dataset / "manifest.json" if dataset.is_dir() else None
    return {
        "path": _relative_to_workspace(workspace, dataset),
        "manifest": _file_metadata(workspace, manifest_path),
        "cases": _manifest_cases(manifest_path),
        "content_sha256": _dataset_hash(manifest_path),
    }


def _dataset_hash(manifest_path: Path | None) -> str | None:
    if manifest_path is None or not manifest_path.exists():
        return None
    dataset_path = manifest_path.parent
    digest = hashlib.sha256()
    _update_digest_with_file(digest, manifest_path)
    for case_name in _manifest_cases(manifest_path):
        _update_digest_with_file(digest, dataset_path / "cases" / case_name)
    return digest.hexdigest()


def _file_metadata(workspace: Path, path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return {
        "path": _relative_to_workspace(workspace, path),
        "sha256": _file_hash(path),
    }


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    _update_digest_with_file(digest, path)
    return digest.hexdigest()


def _update_digest_with_file(digest: Digest, path: Path) -> None:
    digest.update(path.as_posix().encode("utf-8"))
    digest.update(b"\0")
    if path.exists():
        digest.update(path.read_bytes())


def _manifest_cases(manifest_path: Path | None) -> list[str]:
    if manifest_path is None or not manifest_path.exists():
        return []
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = raw.get("cases", []) if isinstance(raw, dict) else []
    return [str(case) for case in cases] if isinstance(cases, list) else []


def _workspace_path(workspace: Path, value: Any) -> Path | None:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return workspace / path


def _relative_to_workspace(workspace: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
