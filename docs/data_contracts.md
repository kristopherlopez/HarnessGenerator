# Data Contracts

Machine-readable defaults live in `bootstrap/`. Workspace-specific contracts live in `workspaces/<workspace_id>/contracts/` and can override global defaults for a task family.

The long-term contract system is task-agnostic. The current defaults are seeded from the YouTube speaker-attribution workspace and should be treated as first-workspace defaults until generic defaults and task adapters are introduced.

## Contract Files

- `domain_contract.yaml`: task family, domain assumptions, and task-specific risk policy.
- `input_contract.yaml`: accepted task inputs and required metadata.
- `output_contract.yaml`: required output artifact shape and validation rules.
- `tool_registry.yaml`: allowed provider interfaces, tool permissions, and prohibited uses.
- `strategy_space.yaml`: candidate generation options and runnable harness or strategy names.
- `harness_search_space.yaml`: allowed harness change surfaces and staged unlocks.
- `metric_contract.yaml`: optimization metrics, selection rules, and disqualifying constraints.
- `safety_contract.yaml`: task safety rules, privacy rules, review gates, and change-control rules.
- `dataset_manifest.yaml`: expected eval dataset groups.
- `codex_task_policy.yaml`: required generated-task structure.

## Workspace Contract Requirements

Before optimization starts, a workspace contract set must define:

- what inputs a harness may read
- what output shape a harness must produce
- how outputs are validated before scoring
- which metrics decide winners
- which constraints disqualify candidates
- which tools and providers are allowed
- which budget limits apply
- which harness change surfaces are allowed
- which generated-task fields are mandatory
- which labels, examples, traces, or aggregate feedback are hidden from candidates

An eval set without these contracts is not enough for HarnessGenerator to run safely.

## Contract Rules

- Public output schemas are stable unless a task explicitly asks to change them.
- Thresholds and scoring cutoffs must live in config, not scattered across task logic.
- Human-reviewed labels are authoritative when the task family has human review.
- Hidden labels must never be visible to candidate strategies.
- Sensitive task internals must not be returned from public APIs or candidate-visible traces.

For the YouTube speaker-attribution workspace, sensitive internals include raw face embeddings, voice embeddings, face crops, raw frames, and private reference clips.
