# To-Do: Eval Runner, Archive, And Traces

## Goal

Generalize the execution loop so every workspace can run candidates under controlled budgets and preserve auditable evidence.

## Checklist

- [ ] Define a generic run config:
  - workspace
  - dataset split
  - baseline or candidate id
  - model/provider config
  - budget limits
  - tool policy
  - repetition count
  - random seed where applicable
- [ ] Add a run archive layout that is independent of task family.
- [ ] Save immutable run evidence:
  - run config
  - candidate source or config snapshot
  - dataset fingerprint
  - output artifacts
  - metrics
  - failure report
  - trace summaries
  - budget usage
- [ ] Add trace capture hooks for:
  - model calls
  - tool calls
  - retries
  - validation failures
  - exceptions
  - timing
- [ ] Redact secrets from traces and errors.
- [ ] Keep hidden labels out of candidate-visible traces.
- [ ] Add output-contract validation before scoring.
- [ ] Add budget enforcement for:
  - wall-clock time
  - token count
  - model calls
  - tool calls
  - estimated cost
- [ ] Support deterministic and stochastic candidate runs.
- [ ] Add report links from latest reports to archived evidence.

## Initial Slice Completed

- `evals.run_eval` now delegates dataset loading, strategy lookup, scoring, prediction serialization, and failure reporting to workspace adapters.
- `evals.compare_strategies` now delegates strategy comparison eligibility and winner selection to workspace adapters.
- Reports now include `task_type` so mixed workspace output is easier to audit.

Remaining work includes run configs, archives, traces, budget enforcement, output-contract validation, and dataset fingerprints.

## Acceptance Criteria

- Every eval run can be reproduced from a saved config and candidate snapshot.
- Reports include budget usage and contract violations, not only task score.
- Hidden labels are never written into candidate-visible traces.
- Existing YouTube reports continue to work or are migrated with clear compatibility notes.

## Suggested Verification

```powershell
uv run pytest
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```
