# To-Do: Adapter Interfaces

## Goal

Introduce generic interfaces so evals, scoring, strategy lookup, failure mining, and candidate generation do not import YouTube speaker-attribution code directly.

## Checklist

- [x] Define a task adapter interface with responsibilities for:
  - loading datasets
  - listing baselines and candidate strategies
  - scoring predictions
  - mining failures
  - serializing predictions
  - checking strategy eligibility
  - selecting comparison winners
- [ ] Extend adapter responsibilities for:
  - validating inputs
  - validating outputs
  - running one task instance through a generic harness runner
  - proposing candidate changes
- [ ] Define separate protocols where useful:
  - `DatasetAdapter`
  - `HarnessStrategy`
  - `OutputValidator`
  - `MetricScorer`
  - `FailureMiner`
  - `CandidateTemplateProvider`
- [x] Add adapter selection to `task.yaml`, such as an adapter module path or registered task type.
- [ ] Replace direct generic imports of identity code in:
  - `evals/dataset.py`
  - `evals/metrics.py`
  - `app/harness_optimizer/candidates.py`
  - `app/harness_optimizer/next_task.py`
- [x] Route `evals.run_eval.py` through task adapter selection.
- [x] Route `evals.compare_strategies.py` through task adapter selection.
- [x] Implement a YouTube speaker-attribution adapter that wraps the existing identity models and strategies.
- [x] Implement a tiny fake non-YouTube adapter for tests.
- [ ] Document the adapter lifecycle:
  - workspace readiness
  - baseline eval
  - strategy comparison
  - failure mining
  - candidate proposal
  - generated Codex task

## Acceptance Criteria

- Generic strategy-comparison commands no longer need to import `app.identity` directly.
- Generic eval commands no longer need to import `app.identity` directly.
- The YouTube workspace still produces the same reports.
- A fake non-YouTube workspace can run adapter-backed eval and strategy comparison in tests.

## Initial Slice Completed

- Added `app.adapters` with `TaskAdapter` and `HarnessStrategy` protocols.
- Added adapter resolution by workspace manifest `adapter` or `workspace_id`.
- Routed `evals.run_eval` and `evals.compare_strategies` through task adapters.
- Added a YouTube adapter that wraps the existing identity dataset, strategy, metric, and failure-report code.
- Added a `simple_qa` adapter that runs a deterministic exact-match baseline eval.

Remaining work includes finer-grained adapter protocols, output validation, candidate template
providers, and moving candidate generation and next-task code behind adapters.

## Suggested Verification

```powershell
uv run pytest
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
uv run python -m evals.run_eval --workspace tests/fixtures/workspaces/simple_qa --dataset tiny
uv run python -m evals.compare_strategies --workspace tests/fixtures/workspaces/simple_qa --dataset tiny
```
