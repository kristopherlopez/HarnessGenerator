# To-Do: Generic Contract System

## Goal

Make contract loading and validation task-agnostic while preserving workspace-specific overrides.

## Checklist

- [ ] Split contract concepts into generic contracts and task-specific contracts.
- [ ] Add `schema_version` and `task_type` to contract files where missing.
- [ ] Replace identity-specific assumptions in generic contract models, including:
  - required `identity_policy`
  - required `resolution_status` values
  - required speaker fields
  - false-assignment-only metric assumptions
- [ ] Keep a way for a workspace to define stricter requirements, such as speaker identity provenance.
- [ ] Validate required contract file presence for every workspace.
- [ ] Validate that workspace overrides do not silently omit required sections.
- [ ] Add a generic contract fixture for a non-YouTube task, such as structured QA or math word problems.
- [ ] Keep compatibility tests for the YouTube workspace contracts.
- [ ] Update `docs/contracts/data_contracts.md` to separate:
  - engine-level contract requirements
  - task-family contract requirements
  - workspace override behavior

## Acceptance Criteria

- A non-YouTube workspace can load contracts without needing identity-resolution fields.
- The YouTube workspace can still require `unknown`, `needs_review`, provenance, and false-assignment constraints.
- Contract validation errors identify the exact missing or invalid contract section.

## Suggested Verification

```powershell
uv run pytest tests/test_contracts.py
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
```
