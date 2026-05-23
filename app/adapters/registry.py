from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.adapters.base import TaskAdapter
from app.adapters.simple_qa import SimpleQaAdapter
from app.adapters.youtube_speaker_attribution import YouTubeSpeakerAttributionAdapter

DEFAULT_ADAPTER_KEY = "youtube_speaker_attribution"
DEFAULT_STRATEGY = "review_heavy_low_false_assignment"


def resolve_task_adapter(workspace: Path | None) -> TaskAdapter:
    adapter_key = _adapter_key(workspace)
    if adapter_key == "youtube_speaker_attribution":
        return YouTubeSpeakerAttributionAdapter()
    if adapter_key == "simple_qa":
        return SimpleQaAdapter()
    raise ValueError(
        f"Unknown task adapter '{adapter_key}'. Add a task adapter or set a supported "
        "workspace_id/adapter in task.yaml."
    )


def default_strategy_name(workspace: Path | None) -> str:
    if workspace is None:
        return DEFAULT_STRATEGY
    manifest = _load_manifest(workspace)
    strategy = manifest.get("default_strategy") or manifest.get("default_harness")
    if not strategy:
        raise ValueError(
            f"{workspace / 'task.yaml'} must define default_strategy or default_harness"
        )
    return str(strategy)


def _adapter_key(workspace: Path | None) -> str:
    if workspace is None:
        return DEFAULT_ADAPTER_KEY
    manifest = _load_manifest(workspace)
    return str(manifest.get("adapter") or manifest.get("workspace_id") or DEFAULT_ADAPTER_KEY)


def _load_manifest(workspace: Path) -> dict[str, Any]:
    task_path = workspace / "task.yaml"
    if not task_path.exists():
        raise FileNotFoundError(f"Missing workspace manifest: {task_path}")
    loaded = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{task_path} must contain a YAML object")
    return loaded
