# Architecture

## Conceptual Model

HarnessGenerator has two loops:

- **Inner loop:** a candidate harness solves a task instance using models, tools, memory, verification, and stopping rules.
- **Outer loop:** an optimizer proposes candidate harness changes, evaluates them, analyzes failures, and archives useful discoveries.

The outer loop must never rely on hidden test answers. It should optimize on development data and reserve held-out evaluation for final checks.

## Artifact Flow

The engine should distinguish the harness, the task output, and the metadata produced by a run:

```text
Task inputs + gold outputs
   |
   v
Outer-loop proposer creates a harness hypothesis
   |
   v
Runner executes the harness through the Harness API
   |
   v
Harness run result: predicted outputs + traces + budget usage + validation status
   |
   v
Evaluator compares predicted outputs to gold outputs
   |
   v
Metrics + diffs + failure report + optimizer decision
   |
   v
Next harness hypothesis or generated Codex task
```

The Harness API is the execution boundary. It is not the task output. A harness can produce a
task-specific output, but the runner also needs metadata about how that output was produced so the
outer loop can compare, debug, and safely revise the candidate.

## Components

### Current Implementation Notes

The current repo implements the outer-loop skeleton for the YouTube speaker-attribution workspace:
contract loading, workspace readiness, fixture dataset loading, identity strategies, metrics,
failure reports, strategy comparison, regression checks, candidate proposal generation, and
generated Codex tasks.

`app.adapters` defines the generic task-adapter boundary and currently includes adapters for
YouTube speaker attribution and a tiny `simple_qa` fixture. `evals.run_eval` and
`evals.compare_strategies` use this adapter boundary. Candidate proposal templates and next-task
generation still retain first-workspace assumptions and are tracked in `docs/to-do/`.

Each workspace needs data-provisioning pre-work before the optimizer can use it safely. The
workspace should define where task instances come from, what permissions or licenses apply, how raw
or source material becomes draft, review, and gold cases, what provider outputs may be cached, and
which manifests prove the resulting dataset is reproducible. The generic engine should depend on
the prepared cases, contracts, manifests, and adapter API; task-specific acquisition and preparation
logic belongs to the workspace or its adapter.

For the first workspace, local or user-authorized YouTube media preparation, diarized transcription,
and seed-gold calibration are examples of this workspace data-provisioning layer. They are not
global HarnessGenerator requirements.

### Task Spec

Defines the problem family:

- Input schema.
- Expected output schema.
- Dataset locations and split policy.
- Allowed tools.
- Scoring rules.
- Runtime, cost, and safety constraints.

### Dataset Adapter

Loads examples into task-specific case objects behind a common adapter protocol. Current adapters
load manifest-backed fixture directories; future adapters can add JSONL or benchmark-specific
formats without changing the eval entrypoints.

### Workspace Data Provisioning

Defines how usable evaluation cases are created before harness optimization begins. A workspace
should document:

- raw or source data locations and access rules
- transformation steps from source material to task cases
- cache policy for provider outputs and intermediate artifacts
- human-review or gold-label promotion rules
- dataset manifests and split membership
- privacy, licensing, and safety constraints

Candidate harnesses should consume the prepared workspace cases. Direct access to raw source data
should be a deliberate workspace tool-policy decision, not an implicit engine behavior.

### Candidate Harness

A runnable implementation of a strategy or a structured hypothesis about how to solve the task. A
harness can include:

- Prompt templates.
- Context selection.
- Decomposition.
- Tool routing.
- Candidate generation.
- Verification.
- Ensemble or voting logic.
- Stopping rules.

Early harnesses can be simple strategy objects. Later harnesses should be structured candidates
whose prompt, tool, model, verification, retry, and stopping-rule choices are explicit and
archivable.

### Harness API

Defines how the runner executes a candidate harness. Conceptually:

```python
run(case, context) -> harness_run_result
```

The API should provide:

- one stable execution entrypoint
- a run context with approved tools, providers, budgets, workspace config, and trace writer
- no direct access to hidden labels or private test feedback
- structured predicted outputs
- trace events for model calls, tool calls, retries, validation, and errors
- cost, latency, timeout, and budget metadata
- output-contract and safety-contract validation status

The API lets the optimizer search over harness hypotheses without letting candidate code bypass
contracts, hidden-label boundaries, or tool policy.

### Runner

Executes a candidate harness against a split. Responsibilities:

- Start each task with clean state.
- Enforce time, token, retry, and cost budgets.
- Mock or sandbox tools when needed.
- Capture traces.
- Return structured results.

### Evaluator

Compares predicted task outputs to gold outputs and computes scores from candidate outputs and
traces:

- Exact match or unit-test pass rate.
- Rubric-based LLM judge score.
- Cost and latency.
- Step efficiency.
- Tool-call correctness.
- Policy or safety violations.
- Robustness under repeated sampling.

### Archive

Stores every candidate and run:

```text
runs/
└── 2026-05-16T090000Z-example/
    ├── run.yaml
    ├── candidates/
    │   ├── baseline/
    │   └── candidate-001/
    ├── traces/
    ├── scores.json
    ├── failure-analysis.md
    └── report.md
```

### Outer-Loop Proposer

Generates the next harness hypothesis. Early versions should mutate structured config. Later
versions can propose code patches inside a restricted harness API.

Inputs:

- Task spec.
- Baseline harness.
- Prior candidate source.
- Scorecards.
- Gold-comparison diffs.
- Trace summaries.
- Failure analysis.
- Budget constraints.

Outputs:

- Candidate harness hypothesis, source, or config.
- Design rationale.
- Expected impact.
- Risk notes.
- Optimizer decision such as accept, reject, revise, or generate Codex task.

### Reporter

Creates an experiment package:

- Summary table.
- Metric deltas.
- Budget usage.
- Top failures.
- Overfitting checks.
- Recommended next experiments.

## Data Boundaries

- `dev`: examples available to proposer and evaluator during optimization.
- `validation`: examples used to choose candidates.
- `test`: held-out examples used only for final measurement.
- `private`: labels or cases never exposed to candidate harness source, prompts, or traces.

## Candidate Search Levels

1. Prompt and instruction changes.
2. Structured harness config changes.
3. Strategy changes: decomposition, retries, verification, voting.
4. Model and tool routing changes.
5. Restricted code generation.
6. Open-ended code generation with strong sandboxing and review gates.

## Failure Modes

- Overfitting to validation examples.
- Hidden-answer leakage through traces or filesystem access.
- LLM judge drift.
- Candidate code escaping the sandbox.
- Cost blowups from retries or ensembles.
- Improvements that transfer to one model but not another.
- Trace volume becoming too large for useful analysis.
