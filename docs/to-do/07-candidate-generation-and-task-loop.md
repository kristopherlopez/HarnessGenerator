# To-Do: Candidate Generation And Task Loop

## Goal

Generalize the failure-to-candidate-to-Codex-task loop so it can work for any workspace with its own failure taxonomy and allowed change surfaces.

## Checklist

- [ ] Move identity-specific candidate templates behind a YouTube adapter or workspace template provider.
- [ ] Define a generic candidate proposal schema:
  - candidate id
  - failure type
  - affected cases
  - change surface
  - expected metric effect
  - risk notes
  - files likely to change
  - files not to change
  - acceptance criteria
  - required commands
  - safety checks
- [ ] Let each workspace define failure categories and prioritization rules.
- [ ] Let each workspace define candidate template families.
- [ ] Keep global constraints that apply to every task:
  - no broad rewrites
  - no hidden-label access
  - no safety weakening without explicit task
  - no live external APIs in tests unless explicitly allowed
- [ ] Make generated Codex tasks include readiness status and run/report references.
- [ ] Require every candidate to declare its change surface.
- [ ] Add candidate rejection reasons when proposals are unsafe or outside the active phase.
- [ ] Keep candidate generation separate from applying code changes.
- [ ] Add tests for:
  - no-failure hardening task
  - task-specific failure template
  - blocked unsafe candidate
  - missing workspace template provider

## Acceptance Criteria

- Candidate proposals for YouTube still include speaker-attribution-specific risk notes.
- Candidate proposals for a fake workspace do not mention identity, speakers, biometrics, or YouTube.
- Generated Codex tasks remain narrow and testable.

## Suggested Verification

```powershell
uv run pytest tests/test_candidate_proposals.py tests/test_next_task.py
uv run python -m app.harness_optimizer.candidates --workspace workspaces/youtube_speaker_attribution
uv run python -m app.harness_optimizer.next_task --workspace workspaces/youtube_speaker_attribution
```
