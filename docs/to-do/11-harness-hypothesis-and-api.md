# To-Do: Harness Hypothesis And API

## Goal

Define the stable artifacts and execution API that let HarnessGenerator generate a harness
hypothesis, run it against task inputs, compare its predicted outputs to gold outputs, archive run
metadata, analyze failures, and propose the next hypothesis.

## Checklist

- [x] Define the artifact vocabulary:
  - task input
  - gold output
  - predicted task output
  - harness hypothesis
  - Harness API
  - harness run result
  - evaluation output
  - optimizer output
- [x] Define a `HarnessHypothesis` schema with fields for:
  - harness id and version
  - task type and contract versions
  - declared change surface
  - prompts or prompt templates
  - model/provider routing
  - tool policy and tool calls allowed
  - decomposition steps
  - verification checks
  - retry and stopping rules
  - confidence, abstention, or review policy
  - expected budget impact
- [x] Define a `HarnessRunRequest` schema with:
  - workspace id
  - dataset split or case id
  - task input
  - harness hypothesis reference
  - run config
  - budget limits
  - allowed tools/providers
- [x] Define a `HarnessRunResult` schema with:
  - predicted task output
  - output validation status
  - safety validation status
  - trace events
  - model calls
  - tool calls
  - retries
  - errors
  - cost and latency
  - reproducibility metadata
- [x] Define an `EvaluationResult` schema with:
  - gold comparison
  - per-case metrics
  - aggregate metrics
  - constraint violations
  - failure categories
  - scorer version
- [x] Define an `OptimizerDecision` schema with:
  - accept, reject, revise, or generate task
  - rationale
  - target failure types
  - proposed change surface
  - next harness hypothesis or Codex task
  - risk notes
- [x] Update the runner so adapters return harness run results, not only raw predictions.
- [x] Update reports to store the harness hypothesis and run result metadata separately.
- [x] Update candidate generation so generated candidates are explicit harness hypotheses rather than only natural-language task suggestions.
- [x] Add tests that prove:
  - the Harness API is not confused with task output
  - hidden gold outputs are not visible during harness execution
  - run metadata is archived separately from predicted task outputs
  - a simple non-YouTube workspace can run through the same API

## Current Implementation Notes

The first implementation is a compatibility layer around registered strategies:

- `app/harness/models.py` defines the serializable artifact schemas.
- `app/harness/runner.py` builds registered-strategy hypotheses and run results.
- `evals/run_eval.py` now writes `harness_hypothesis`, `harness_run_results`, and
  `harness_run_summary` alongside existing task predictions and metrics.
- `evals/compare_strategies.py` records per-strategy hypotheses and run summaries without changing
  the existing comparison result shape.
- Candidate proposal output includes a structured `harness_hypothesis` for each proposed change and
  materializes runnable config-only harness candidates under `experiments/generated_harnesses/`.
- `evals/run_eval.py --harness <path-or-id>` can run a generated harness config without promoting it.

Remaining work: replace the compatibility runner with provider-aware execution contexts, add output
and safety validators inside the runner, implement `LlmReasoner` provider bindings, and store full
optimizer decisions as first-class report artifacts.

## Acceptance Criteria

- The docs and code use the same artifact names.
- A harness hypothesis can be serialized before execution.
- A run result can be archived and replayed or audited.
- The evaluator compares predicted task outputs to gold outputs without exposing hidden labels to the harness.
- Candidate generation emits a structured next hypothesis or a narrow Codex task.

## Suggested Verification

```powershell
uv run pytest
uv run ruff check .
uv run mypy app evals
uv run python -m evals.run_eval --workspace tests/fixtures/workspaces/simple_qa --dataset tiny
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```
