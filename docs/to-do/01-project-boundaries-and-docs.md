# To-Do: Project Boundaries And Docs

## Goal

Make it unambiguous that HarnessGenerator is the reusable engine, while YouTube speaker attribution is the first task workspace and MVP benchmark.

## Checklist

- [x] Update root documentation to distinguish:
  - generic HarnessGenerator concepts
  - current YouTube speaker-attribution workspace
  - currently mixed areas that need extraction
- [x] Add a "What a workspace must provide" section to the project docs.
- [x] Add a "Generic vs workspace-specific" map for:
  - contracts
  - datasets
  - harnesses
  - eval runners
  - metrics
  - failure mining
  - candidate generation
  - provider/tool policy
- [x] Clarify that root-level defaults are not supposed to encode one task family permanently.
- [x] Mark task-family docs such as resolver strategies and speaker-attribution failure modes as YouTube-workspace docs, or move them under `workspaces/youtube_speaker_attribution/docs/`.
- [x] Update the roadmap to include workspace onboarding and readiness gating before optimization.
- [x] Add a glossary for:
  - workspace
  - task family
  - task adapter
  - candidate harness
  - baseline harness
  - eval split
  - hidden labels
  - failure miner
  - change surface

## Acceptance Criteria

- A new contributor can tell which docs apply to every workspace and which apply only to YouTube speaker attribution.
- The docs state that an eval set alone is not enough to run HarnessGenerator.
- No implementation behavior changes are required for this task.

## Suggested Verification

```powershell
uv run ruff check .
```
