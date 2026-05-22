# To-Do: Adapter Interfaces

## Goal

Introduce generic interfaces so evals, scoring, strategy lookup, failure mining, and candidate generation do not import YouTube speaker-attribution code directly.

## Checklist

- [ ] Define a task adapter interface with responsibilities for:
  - loading datasets
  - validating inputs
  - validating outputs
  - listing baselines and candidate strategies
  - running one task instance
  - scoring predictions
  - mining failures
  - proposing candidate changes
- [ ] Define separate protocols where useful:
  - `DatasetAdapter`
  - `HarnessStrategy`
  - `OutputValidator`
  - `MetricScorer`
  - `FailureMiner`
  - `CandidateTemplateProvider`
- [ ] Add adapter selection to `task.yaml`, such as an adapter module path or registered task type.
- [ ] Replace direct generic imports of identity code in:
  - `evals/dataset.py`
  - `evals/metrics.py`
  - `evals/run_eval.py`
  - `evals/compare_strategies.py`
  - `app/harness_optimizer/candidates.py`
  - `app/harness_optimizer/next_task.py`
- [ ] Implement a YouTube speaker-attribution adapter that wraps the existing identity models and strategies.
- [ ] Implement a tiny fake non-YouTube adapter for tests.
- [ ] Document the adapter lifecycle:
  - workspace readiness
  - baseline eval
  - strategy comparison
  - failure mining
  - candidate proposal
  - generated Codex task

## Acceptance Criteria

- Generic eval commands no longer need to import `app.identity` directly.
- The YouTube workspace still produces the same reports.
- A fake non-YouTube workspace can run a baseline eval in tests.

## Suggested Verification

```powershell
uv run pytest
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```
