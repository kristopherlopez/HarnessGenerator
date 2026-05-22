# To-Do: CI And Regression Gates

## Goal

Add automated checks that keep generic engine work and workspace-specific behavior from drifting apart.

## Checklist

- [x] Add a small generic fake workspace used only for tests.
- [x] Add tests that run readiness on:
  - the fake workspace
  - the YouTube workspace
  - an intentionally incomplete workspace
- [ ] Add tests that run baseline eval on the fake workspace.
- [ ] Add tests that confirm YouTube evals still use speaker-attribution metrics.
- [ ] Add tests that candidate proposal generation is task-specific.
- [ ] Add tests that generated tasks include required policy fields.
- [ ] Add tests that hidden labels are not present in candidate-visible traces.
- [ ] Add tests that output-contract violations fail before scoring.
- [ ] Add tests that safety-contract violations disqualify candidates.
- [ ] Add CI commands for:
  - unit tests
  - lint
  - type checks
  - bootstrap/readiness validation
  - YouTube workspace regression check
- [ ] Add docs explaining which checks are required for:
  - generic engine PRs
  - workspace-only PRs
  - provider/tool PRs
  - safety-contract PRs

## Acceptance Criteria

- A generic engine change cannot accidentally break the YouTube workspace without test failure.
- A YouTube workspace change cannot accidentally introduce generic engine assumptions without test failure.
- Incomplete workspaces cannot pass readiness.
- CI output tells maintainers which layer failed.

## Initial Slice Completed

- Added `tests/fixtures/workspaces/simple_qa` as a non-YouTube readiness fixture.
- Confirmed the fake workspace can pass readiness with a generic `output_schema` and without speaker/identity output fields.
- Kept full fake-workspace eval support for the later adapter-interface work.

## Suggested Verification

```powershell
uv run pytest
uv run ruff check .
uv run mypy app evals
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
uv run python -m evals.check_regression --workspace workspaces/youtube_speaker_attribution
```
