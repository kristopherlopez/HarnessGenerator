# To-Do: Readiness Validation Gate

## Goal

Prevent HarnessGenerator from running candidate generation or optimization against an incomplete, unsafe, or unscorable workspace.

## Checklist

- [ ] Define readiness stages:
  - `scaffolded`
  - `contracts_ready`
  - `fixture_ready`
  - `baseline_ready`
  - `optimization_ready`
- [x] Extend or replace `app.bootstrap.readiness` with a workspace readiness command, for example:

```powershell
uv run python -m app.workspaces.readiness --workspace workspaces/example_task
```

- [x] Validate `task.yaml`:
  - workspace id is present
  - default dataset is present
  - default baseline or strategy is present
  - declared paths exist
- [ ] Validate contracts:
  - required files exist
  - schemas validate
  - output contract is explicit
  - safety contract is explicit
  - metric contract has selection rules
  - tool policy is explicit
- [ ] Validate datasets:
  - manifest exists
  - at least one tiny labelled fixture exists
  - split policy exists
  - hidden labels are not exposed to candidate code
- [ ] Validate baseline:
  - baseline harness or strategy is registered
  - baseline can run on the tiny fixture
  - baseline output validates against the output contract
- [ ] Validate scoring:
  - scorer runs on baseline output
  - primary metric is produced
  - constraints can be evaluated
- [ ] Validate reporting:
  - reports directory is writable
  - run archive directory is writable
  - readiness report is written as JSON and Markdown
- [ ] Make eval, comparison, candidate proposal, and next-task commands refuse workspaces below `optimization_ready`.
- [ ] Add an override only for explicit development use, such as `--allow-not-ready`, and log it in reports.

## Acceptance Criteria

- Candidate generation is blocked when required workspace pieces are missing.
- Readiness output tells the user exactly what remains to be configured.
- The YouTube workspace passes the new readiness gate.
- A scaffolded incomplete workspace fails with actionable messages.

## Initial Slice Completed

- Added `uv run python -m app.workspaces.readiness --workspace ...`.
- Validates `task.yaml`, declared paths, merged contract loading, default dataset manifest, default strategy declaration, and reports writability.
- Writes `workspace_readiness.json`.
- Includes tests for the YouTube workspace and incomplete workspaces.

Remaining work includes staged readiness states, deeper dataset and baseline/scorer validation, Markdown reports, command blocking, and an explicit development override.

## Suggested Verification

```powershell
uv run pytest
uv run python -m app.workspaces.readiness --workspace workspaces/youtube_speaker_attribution
uv run python -m app.harness_optimizer.candidates --workspace workspaces/youtube_speaker_attribution
```
