from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from app.workspaces import resolve_workspace


def load_workspace_loops(workspace: Path | str) -> dict[str, dict[str, Any]]:
    workspace_path = Path(workspace)
    task_path = workspace_path / "task.yaml"
    if not task_path.exists():
        raise FileNotFoundError(f"Missing workspace manifest: {task_path}")

    loaded = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{task_path} must contain a YAML object")

    raw_loops = loaded.get("workspace_loops", {})
    if not isinstance(raw_loops, dict):
        raise ValueError("task.yaml field 'workspace_loops' must be an object")

    loops: dict[str, dict[str, Any]] = {}
    for name, loop in raw_loops.items():
        if not isinstance(name, str):
            raise ValueError("workspace loop names must be strings")
        if not isinstance(loop, dict):
            raise ValueError(f"workspace loop '{name}' must be an object")
        loops[name] = loop
    return loops


def render_loop(name: str, loop: dict[str, Any]) -> str:
    description = str(loop.get("description", "")).strip()
    when_to_use = str(loop.get("when_to_use", "")).strip()
    commands = loop.get("commands", [])
    if not isinstance(commands, list):
        raise ValueError(f"workspace loop '{name}' commands must be a list")

    lines = [f"# {name}"]
    if description:
        lines.extend(["", description])
    if when_to_use:
        lines.extend(["", f"When to use: {when_to_use}"])
    if commands:
        lines.extend(["", "Commands:"])
        for command in commands:
            lines.append(f"- `{command}`")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show named workspace loops.")
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List named loops.")
    show = subparsers.add_parser("show", help="Show one named loop.")
    show.add_argument("loop_name")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise ValueError("--workspace is required")

    loops = load_workspace_loops(workspace)
    command = args.command or "list"
    if command == "list":
        if args.json:
            print(json.dumps({"loops": sorted(loops)}, indent=2))
            return
        for name in sorted(loops):
            description = str(loops[name].get("description", "")).strip()
            print(f"{name}: {description}" if description else name)
        return

    if command == "show":
        loop_name = args.loop_name
        if loop_name not in loops:
            available = ", ".join(sorted(loops))
            raise SystemExit(f"Unknown loop '{loop_name}'. Available loops: {available}")
        if args.json:
            print(json.dumps({loop_name: loops[loop_name]}, indent=2))
            return
        print(render_loop(loop_name, loops[loop_name]))
        return

    parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
