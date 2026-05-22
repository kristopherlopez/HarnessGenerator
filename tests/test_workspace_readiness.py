from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.workspaces.readiness import validate_workspace_readiness

YOUTUBE_WORKSPACE = Path("workspaces/youtube_speaker_attribution")


def test_youtube_workspace_passes_basic_readiness(tmp_path: Path) -> None:
    output = tmp_path / "workspace_readiness.json"
    report = validate_workspace_readiness(YOUTUBE_WORKSPACE, output_path=output)

    assert report.ready
    assert report.status == "optimization_ready"
    assert {check.name for check in report.checks} >= {
        "task_manifest",
        "contracts",
        "declared_paths",
        "default_dataset",
        "default_strategy",
        "reports_writable",
    }
    assert all(check.status == "pass" for check in report.checks)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "optimization_ready"


def test_incomplete_workspace_fails_with_actionable_messages(tmp_path: Path) -> None:
    workspace = tmp_path / "incomplete_workspace"
    workspace.mkdir()
    (workspace / "task.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 0.1,
                "workspace_id": "incomplete_workspace",
                "default_dataset": "tiny",
                "paths": {
                    "contracts": "contracts",
                    "datasets": "datasets",
                    "reports": "reports",
                },
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "readiness.json"
    report = validate_workspace_readiness(workspace, output_path=output)

    assert not report.ready
    messages = "\n".join(check.message for check in report.checks if check.status == "fail")
    assert "default_strategy or default_harness" in messages
    assert "Missing workspace contracts directory" in messages
    assert "Missing declared paths" in messages
    assert "Default dataset is missing" in messages


def test_workspace_readiness_requires_task_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "missing_manifest"
    workspace.mkdir()

    report = validate_workspace_readiness(workspace, output_path=tmp_path / "readiness.json")

    assert not report.ready
    assert any(check.name == "task_manifest" for check in report.checks)

