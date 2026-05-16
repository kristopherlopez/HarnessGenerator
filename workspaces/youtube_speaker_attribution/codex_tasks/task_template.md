# Codex Task: <short title>

## Observed Failure

Describe the failure observed in eval output.

## Affected Cases

- `<dataset> <case_id> <segment_id>`

## Suspected Cause

Explain the likely implementation or strategy cause.

## Required Change

Describe one narrow change.

## Files Likely To Change

- `app/...`
- `tests/...`
- `docs/...`

## Files Not To Change

- `bootstrap/output_contract.yaml`
- `bootstrap/safety_contract.yaml`

## Acceptance Criteria

- Tests cover the failure.
- Relevant eval metric improves or remains within allowed bounds.
- False-assignment rate does not exceed the configured limit.
- Output and safety contracts are preserved.

## Required Tests

```powershell
uv run pytest
```

## Required Eval Command

```powershell
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

## Safety Checks

- No identity assignment without provenance.
- No live external APIs in tests.
- No public exposure of biometric internals.
