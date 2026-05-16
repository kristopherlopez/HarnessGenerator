# Data Contracts

Machine-readable defaults live in `bootstrap/`. Workspace-specific contracts live in `workspaces/<workspace_id>/contracts/` and can override global defaults for a task family.

## Contract Files

- `domain_contract.yaml`: project goal, population assumptions, and identity policy.
- `input_contract.yaml`: accepted media inputs and required metadata.
- `output_contract.yaml`: required transcript, speaker, evidence, and review fields.
- `tool_registry.yaml`: allowed provider interfaces and prohibited LLM uses.
- `strategy_space.yaml`: candidate generation and resolution strategies.
- `harness_search_space.yaml`: allowed Poetiq-style harness change surfaces.
- `metric_contract.yaml`: optimization metrics and winner constraints.
- `safety_contract.yaml`: privacy, review, and false-assignment rules.
- `dataset_manifest.yaml`: expected eval dataset groups.
- `codex_task_policy.yaml`: required generated-task structure.

## Contract Rules

- Public output schemas are stable unless a task explicitly asks to change them.
- Thresholds must live in config, not scattered across resolver code.
- Human-reviewed labels are authoritative.
- Hidden labels must never be visible to candidate strategies.
- Raw biometric internals must not be returned from public APIs.
