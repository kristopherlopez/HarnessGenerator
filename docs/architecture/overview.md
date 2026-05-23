# Architecture

## Conceptual Model

HarnessGenerator has two loops:

- **Inner loop:** a candidate harness solves a task instance using models, tools, memory, verification, and stopping rules.
- **Outer loop:** an optimizer proposes candidate harness changes, evaluates them, analyzes failures, and archives useful discoveries.

The outer loop must never rely on hidden test answers. It should optimize on development data and reserve held-out evaluation for final checks.

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

Media ingestion is available as an opt-in draft-data workflow, not as a fully optimized harness
surface. `app.media` prepares local or user-authorized YouTube media chunks, `app.transcription`
normalizes Deepgram/OpenAI diarized provider output into draft cases, and `app.calibration`
generates seed-gold review material.

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

### Candidate Harness

A runnable implementation of a strategy. A harness can include:

- Prompt templates.
- Context selection.
- Decomposition.
- Tool routing.
- Candidate generation.
- Verification.
- Ensemble or voting logic.
- Stopping rules.

### Runner

Executes a candidate harness against a split. Responsibilities:

- Start each task with clean state.
- Enforce time, token, retry, and cost budgets.
- Mock or sandbox tools when needed.
- Capture traces.
- Return structured results.

### Evaluator

Computes scores from candidate outputs and traces:

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

Generates the next candidate. Early versions should mutate structured config. Later versions can propose code patches inside a restricted harness API.

Inputs:

- Task spec.
- Baseline harness.
- Prior candidate source.
- Scorecards.
- Trace summaries.
- Failure analysis.
- Budget constraints.

Outputs:

- Candidate harness source or config.
- Design rationale.
- Expected impact.
- Risk notes.

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
