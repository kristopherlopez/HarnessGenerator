from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.bootstrap.contracts import load_bootstrap_contracts
from app.workspaces import resolve_workspace, workspace_codex_task_path, workspace_report_path


def generate_next_task(
    eval_report_path: Path,
    failure_report_path: Path,
    output_path: Path,
    workspace: Path | None = None,
) -> Path:
    contracts = load_bootstrap_contracts(workspace=workspace)
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    failure_report = json.loads(failure_report_path.read_text(encoding="utf-8"))
    failures = failure_report.get("failures", [])

    selected_type = _select_failure_type(failures)
    selected_failures = [
        failure for failure in failures if failure.get("failure_type") == selected_type
    ][:5]

    task = _render_task(
        eval_report=eval_report,
        selected_type=selected_type,
        selected_failures=selected_failures,
        policy=contracts.codex_task.generated_task_must_include,
        change_surfaces=contracts.harness_search.change_surfaces,
        candidate_requirements=contracts.harness_search.candidate_requirements,
        workspace=workspace,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(task, encoding="utf-8")
    return output_path


def _select_failure_type(failures: list[dict[str, Any]]) -> str:
    if not failures:
        return "no_failures"
    priority = {
        "false_assignment": 0,
        "unknown_forced_to_known": 1,
        "missed_known_identity": 2,
    }
    counts = Counter(str(failure.get("failure_type")) for failure in failures)
    return sorted(counts, key=lambda item: (priority.get(item, 99), -counts[item]))[0]


def _render_task(
    eval_report: dict[str, Any],
    selected_type: str,
    selected_failures: list[dict[str, Any]],
    policy: list[str],
    change_surfaces: dict[str, list[str]],
    candidate_requirements: list[str],
    workspace: Path | None,
) -> str:
    affected_cases = "\n".join(
        f"- `{failure['case_id']} {failure['segment_id']}`"
        for failure in selected_failures
    )
    if not affected_cases:
        affected_cases = "- No failing cases in the latest report."

    suspected_cause = (
        selected_failures[0].get("suspected_cause", "No suspected cause.")
        if selected_failures
        else "No failures detected; generate a small hardening task."
    )
    strategy = eval_report.get("strategy", "unknown")
    metrics = eval_report.get("metrics", {})
    allowed_surfaces = _suggest_change_surfaces(selected_type, change_surfaces)
    required_commands = _required_eval_commands(workspace)

    return f"""# Codex Task: improve {selected_type.replace("_", " ")}

## Observed Failure

Latest eval strategy: `{strategy}`.

Selected failure type: `{selected_type}`.

Current metrics:

- false_assignment_rate: `{metrics.get("false_assignment_rate", "unknown")}`
- identity_accuracy: `{metrics.get("identity_accuracy", "unknown")}`
- known_person_recall: `{metrics.get("known_person_recall", "unknown")}`
- needs_review_rate: `{metrics.get("needs_review_rate", "unknown")}`

## Affected Cases

{affected_cases}

## Suspected Cause

{suspected_cause}

## Required Change

Make one narrow resolver or eval improvement that addresses `{selected_type}` without weakening the
safety contract. Prefer changes to thresholds, evidence handling, failure classification, or tests
before adding new provider integrations.

## Allowed Harness Change Surfaces

{allowed_surfaces}

## Files Likely To Change

- `app/identity/strategies.py`
- `evals/metrics.py`
- `tests/`
- `docs/failure_modes.md`

## Files Not To Change

- `contracts/output_contract.yaml`
- `contracts/safety_contract.yaml`

## Acceptance Criteria

- Add or update a regression fixture for the observed failure.
- Preserve the output contract.
- Preserve the safety contract.
- Do not increase `false_assignment_rate` above the configured limit.
- Include before/after eval output in the PR notes.
- Declare which harness change surface was modified.

## Candidate Requirements

{_format_bullets(candidate_requirements)}

## Required Tests

```powershell
uv run pytest
```

## Required Eval Command

```powershell
{required_commands}
```

## Safety Checks

- No identity assignment without evidence provenance.
- No live external APIs in tests.
- No public exposure of biometric internals.
- Human-reviewed labels remain authoritative.

## Policy Fields Covered

{", ".join(f"`{item}`" for item in policy)}
"""


def _suggest_change_surfaces(
    selected_type: str,
    change_surfaces: dict[str, list[str]],
) -> str:
    if selected_type in {"false_assignment", "unknown_forced_to_known"}:
        surface_names = ["thresholds_and_policies", "verification", "evidence_strategy"]
    elif selected_type == "missed_known_identity":
        surface_names = ["evidence_strategy", "thresholds_and_policies", "verification"]
    else:
        surface_names = ["verification", "thresholds_and_policies"]

    lines: list[str] = []
    for surface_name in surface_names:
        options = change_surfaces.get(surface_name, [])
        lines.append(f"- `{surface_name}`: {', '.join(f'`{option}`' for option in options)}")
    return "\n".join(lines)


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items)


def _required_eval_commands(workspace: Path | None) -> str:
    if workspace is None:
        return "\n".join(
            [
                "uv run python -m evals.run_eval --dataset evals/datasets/small_gold",
                "uv run python -m evals.compare_strategies --dataset evals/datasets/small_gold",
                "uv run python -m evals.check_regression --report evals/reports/latest.json",
            ]
        )

    workspace_text = workspace.as_posix()
    return "\n".join(
        [
            f"uv run python -m evals.run_eval --workspace {workspace_text} --dataset small_gold",
            (
                "uv run python -m evals.compare_strategies "
                f"--workspace {workspace_text} --dataset small_gold"
            ),
            f"uv run python -m evals.check_regression --workspace {workspace_text}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the next narrow Codex task.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--eval-report", type=Path)
    parser.add_argument("--failure-report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    eval_report = args.eval_report or workspace_report_path(
        workspace,
        "latest.json",
        Path("evals/reports/latest.json"),
    )
    failure_report = args.failure_report or workspace_report_path(
        workspace,
        "latest_failures.json",
        Path("evals/failures/latest_failures.json"),
    )
    output = args.output or workspace_codex_task_path(
        workspace,
        "generated",
        "next_task.md",
        fallback=Path("prompts/codex_tasks/generated/next_task.md"),
    )
    generate_next_task(eval_report, failure_report, output, workspace=workspace)


if __name__ == "__main__":
    main()
