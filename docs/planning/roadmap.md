# Roadmap

## Current Status

The repository has a runnable YouTube speaker-attribution fixture loop, workspace readiness checks,
strategy comparison under safety constraints, generated Codex task/candidate output, a small
non-YouTube `simple_qa` adapter fixture, opt-in media preparation, Deepgram/OpenAI diarized
transcription adapters, and seed-gold review-case generation.

The main remaining extraction work is to route candidate templates, generated tasks, output
validation, traces, archives, and provider policy through generic workspace adapter interfaces.

## Phase 0: Documentation and Scoping

- [x] Create project README and architecture docs.
- [x] Capture research assumptions and Poetiq-inspired principles.
- [x] Define initial task spec and experiment report templates.

## Phase 1: Manual Harness Runner

- [x] Implement bootstrap contract loading.
- [x] Validate `bootstrap/*.yaml` with typed models.
- [x] Generate bootstrap readiness reports.
- [x] Implement workspace manifest loading.
- [x] Implement labelled transcript fixture loading for the first workspace.
- [x] Implement `BaselineUnknownStrategy`.
- [x] Capture scores in JSON reports.
- [ ] Capture full traces.
- [ ] Generate full experiment reports.

Exit criteria:

- One labelled fixture benchmark can be run from a saved config.
- Baseline identity-resolution metrics are reproducible.

## Phase 1A: Workspace Onboarding And Readiness

- [x] Document generic engine boundaries versus first-workspace assumptions.
- [x] Define the required pieces a workspace must provide before optimization.
- [ ] Add a workspace scaffold workflow.
- [x] Add a workspace readiness validator.
- [x] Add a tiny non-YouTube fixture workspace for generic engine tests.
- [ ] Block every optimization path for incomplete workspaces.

Exit criteria:

- A new workspace can be scaffolded without copying the YouTube workspace.
- Readiness reports explain missing contracts, datasets, baselines, scorers, or safety policy.
- The YouTube workspace and a fake non-YouTube workspace both pass their appropriate readiness checks.
- Candidate generation refuses an unready workspace.

## Phase 2: Prompt-Level Optimization

- [x] Add strategy comparison using merged `strategy_space.yaml` contracts.
- [x] Add winner selection using configured strategy constraints.
- [x] Prove that high raw accuracy cannot win when false-assignment constraints are violated.
- [ ] Archive immutable candidates and scorecards.
- [ ] Add validation-vs-test comparison.
- [ ] Add real cost and latency accounting.

Exit criteria:

- Candidate resolver strategies can be run, compared, and reported automatically.

## Phase 3: Strategy Search

- [x] Implement first-workspace failure mining.
- [x] Implement `app.harness_optimizer.next_task`.
- [x] Generate Codex tasks from eval and failure reports.
- [x] Generate bounded candidate proposal tasks.
- [ ] Add configurable diarization/transcription reconciliation, speaker-name resolution, verification, retries, and voting.
- [ ] Move candidate templates behind workspace adapters.
- [ ] Add model transfer evaluation.
- [ ] Add failure clustering.

Exit criteria:

- The system can identify top failures and generate narrow implementation tasks with tests and eval commands.

## Phase 4: Media Providers

- [x] Add local media ingestion and chunk manifest generation.
- [x] Add `ffmpeg` normalization/chunking helpers.
- [x] Add YouTube intake seeding and opt-in `yt-dlp` media preparation helper.
- [x] Add Deepgram and OpenAI diarized transcription adapters.
- [x] Add mocked provider-response tests.
- [x] Add seed-gold calibration and seeded review-case generation.
- [ ] Add generic provider interfaces and policy enforcement.
- [ ] Add optional authorized YouTube caption access.

Exit criteria:

- The eval loop can run on a small local media fixture without live external APIs in tests.

## Phase 5: Restricted Code Search

- Define a narrow Python harness API.
- Add sandboxed candidate execution.
- Add static checks and import allowlists.
- Add rollback and quarantine for failed candidates.

Exit criteria:

- Generated candidate code can be safely evaluated without manual edits.

## Phase 6: Reusable Meta-System

- Add cross-task research memory.
- Add candidate diversity and novelty tracking.
- Add benchmark adapters for coding, RAG, and reasoning tasks.
- Add exportable harness packages.

Exit criteria:

- Lessons from one task family can inform another without leaking labels or hidden test data.
