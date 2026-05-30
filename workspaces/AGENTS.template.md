# AGENTS.md

## Workspace Purpose

Describe this task family and the concrete problem being optimized.

```text
workspaces/<workspace_id>/
```

State what input the workspace accepts, what output it produces, and what safety
or quality property matters most.

This file is task-specific. Do not copy workspace assumptions into the root
`AGENTS.md` or generic harness code unless they become reusable abstractions.

## Read First

Use this order for local context:

1. `task.yaml` for workspace paths, active artifacts, and promotion policy.
2. `docs/<primary_workflow>.md` for the active review or optimization loop.
3. `docs/<task_family>.md` for task-family intent and scope.
4. Contracts only when changing schemas or public outputs.
5. Reports, runs, and codex tasks only when optimizing from eval failures.

Keep this list to 2-5 concrete documents so agents do not load stale context.

## Active Dataset Workflow

- Gold/eval dataset:
- Active review dataset:
- Draft/source dataset:
- Archived/debug datasets:
- Active provider output:
- Active calibration/profile artifact:

Generated review material is not gold until explicitly promoted under this
workspace's promotion policy.

## Human Review Rules

- Define which labels count as human-reviewed.
- Define how to preserve or update human-reviewed labels.
- Define how generated labels become gold.
- Define required provenance for reviewed examples.

## Provider And Tool Rules

- List preferred providers/tools for this task family.
- List cached provider-output locations.
- State when live external APIs may be called.
- State secrets-handling rules.
- State known provider quirks that affect correctness.

## Commands

Run focused checks:

```powershell
uv run pytest <focused tests>
```

Run full checks:

```powershell
uv run ruff check .
uv run mypy app evals
uv run pytest
```

Run workspace eval:

```powershell
uv run python -m evals.run_eval --workspace workspaces/<workspace_id> --dataset <dataset>
```

## Definition Of Done

For data edits:

- schema validation passes
- IDs and manifests remain consistent
- human-reviewed provenance is preserved
- focused dataset tests pass

For harness logic edits:

- tests pass
- lint and type checks pass
- relevant evals/reports run
- failure mode and regression impact are documented

## Review Focus

Prioritize:

- task-specific high-cost failures
- missing provenance
- unsafe promotion of generated artifacts
- hidden assumptions that should remain workspace-local
- regressions in active eval metrics
