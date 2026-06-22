from __future__ import annotations

from pathlib import Path

import yaml

from app.workspaces.loops import load_workspace_loops, render_loop


def test_load_workspace_loops_from_task_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "task.yaml").write_text(
        yaml.safe_dump(
            {
                "workspace_id": "example",
                "workspace_loops": {
                    "refresh_gold_loop": {
                        "description": "Refresh gold artifacts.",
                        "when_to_use": "After promotion.",
                        "commands": ["uv run example"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loops = load_workspace_loops(workspace)

    assert sorted(loops) == ["refresh_gold_loop"]
    assert loops["refresh_gold_loop"]["commands"] == ["uv run example"]


def test_render_loop_includes_description_and_commands() -> None:
    rendered = render_loop(
        "evaluate_harness_loop",
        {
            "description": "Run checks.",
            "when_to_use": "After changes.",
            "commands": ["uv run pytest"],
        },
    )

    assert "# evaluate_harness_loop" in rendered
    assert "Run checks." in rendered
    assert "When to use: After changes." in rendered
    assert "- `uv run pytest`" in rendered
