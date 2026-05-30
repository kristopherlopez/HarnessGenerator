# AGENTS.md

## Project Purpose

This repository builds a recursive harness generator: a meta-system for discovering
which tools, models, prompts, configs, thresholds, and review workflows best solve
a task family.

The repository is intentionally layered. Keep those layers separate.

## Layer Model

### Harness Generator Layer

This is the reusable layer. It lives mostly in:

- `app/`
- `evals/`
- `bootstrap/`
- `tests/`

This layer should answer questions like:

- Which candidate harness change should be tried next?
- Which tool/model/prompt/config combination should be compared?
- Which failure family is currently dominant?
- Which ablation branch should be archived, promoted, or abandoned?
- Which eval/report proves a harness change improved the task?

Do not bake one workspace's dataset layout, provider quirks, or domain assumptions
into this layer unless the abstraction is explicitly reusable and configurable.

### Workspace Layer

Each task family lives under:

```text
workspaces/<workspace_id>/
```

A workspace owns its:

- `task.yaml`
- task-specific `AGENTS.md`
- contracts
- datasets
- provider outputs
- harnesses
- experiments
- runs
- reports
- task-specific docs

Use `workspaces/AGENTS.template.md` when creating a new workspace-level
`AGENTS.md`.

Workspace rules may be stricter or more specific than this file. When working
inside a workspace, read that workspace's `AGENTS.md` before editing data, docs,
contracts, harnesses, or generated outputs.

### Dataset And Provider Layer

Datasets, provider outputs, gold labels, and review drafts are task artifacts.
They belong in the workspace, not in generic harness assumptions. Generated
review material is not gold unless the workspace promotion policy says it is.

## Progressive Disclosure

Before making a change, read only the narrowest docs needed in this order:

1. Root `AGENTS.md` for repository-wide harness rules.
2. `workspaces/<workspace_id>/task.yaml` for workspace identity and paths.
3. `workspaces/<workspace_id>/AGENTS.md` for task-family rules.
4. The specific workspace docs named by that file.
5. Contracts only when changing schemas or public outputs.
6. Reports, runs, and codex tasks only when optimizing or evaluating harness changes.

Do not promote workspace-specific rules back into this file unless they apply to
multiple task families.

## Non-Negotiable Rules

- Prefer `unknown`, `needs_review`, or no assignment over wrong real-person attribution.
- Do not make identity assignments without evidence provenance.
- Do not expose raw face embeddings, voice embeddings, face crops, or raw frames through public API responses.
- Do not overwrite human-reviewed labels. If review status is unclear, inspect workspace rules before editing.
- Do not allow LLM calls to be the only source of identity truth.
- Do not change public API schemas unless the task explicitly asks for it.
- Do not modify safety contracts unless the task explicitly asks for it.
- Do not use live external APIs in tests.
- Do not call live external APIs during task work unless the user explicitly asks or the cached artifact is missing and the task requires regeneration.
- Do not print secrets from `.env` or provider configs.
- Do not add resolver or harness-optimizer logic without tests and a relevant eval/report path.
- Do not hardcode thresholds without adding them to config and docs.

## Commands

Install:

```powershell
uv sync
```

Run tests:

```powershell
uv run pytest
```

Run lint:

```powershell
uv run ruff check .
```

Run type checks:

```powershell
uv run mypy app evals
```

Validate bootstrap contracts for a workspace:

```powershell
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
```

Generate next Codex task for a workspace:

```powershell
uv run python -m app.harness_optimizer.next_task --workspace workspaces/youtube_speaker_attribution
```

Generate candidate harness changes for a workspace:

```powershell
uv run python -m app.harness_optimizer.candidates --workspace workspaces/youtube_speaker_attribution
```

Workspace-specific eval, dataset, and provider commands belong in the workspace
`AGENTS.md` or docs.

## Definition Of Done

A generic harness change is done only when:

- tests pass
- lint passes
- type checks pass when Python code changes
- relevant evals or reports run for resolver, scoring, strategy, or optimizer changes
- identity logic changes include regression tests
- public API contracts are preserved unless explicitly changed
- biometric safety rules are preserved
- docs are updated when contracts, resolver behavior, or workflow behavior changes

Dataset-only or documentation-only changes do not require full before/after evals
unless they alter scoring, contracts, resolver behavior, or optimizer behavior.

## Review Focus

When reviewing PRs, flag:

- harness logic that is secretly specific to one workspace
- false-assignment risk
- false-merge risk
- identity decisions without provenance
- missing open-set unknown handling
- public exposure of biometric internals
- missing regression tests
- metric gaming, especially improving recall while increasing false assignments
- generated artifacts being treated as gold without workspace promotion policy
