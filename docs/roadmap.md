# Roadmap

## Phase 0: Documentation and Scoping

- Create project README and architecture docs.
- Capture research assumptions and Poetiq-inspired principles.
- Define initial task spec and experiment report templates.

## Phase 1: Manual Harness Runner

- Implement bootstrap contract loading.
- Validate `bootstrap/*.yaml` with typed models.
- Generate bootstrap readiness reports.
- Implement task spec loading.
- Implement a JSONL episode manifest adapter.
- Implement labelled transcript fixture loading.
- Implement `BaselineUnknownStrategy`.
- Capture traces and scores.
- Generate experiment reports.

Exit criteria:

- One labelled fixture benchmark can be run from a saved config.
- Baseline identity-resolution metrics are reproducible.

## Phase 2: Prompt-Level Optimization

- Add strategy comparison using `bootstrap/strategy_space.yaml`.
- Add winner selection using `bootstrap/metric_contract.yaml`.
- Prove that high raw accuracy cannot win when false-assignment constraints are violated.
- Archive candidates and scorecards.
- Add validation-vs-test comparison.
- Add cost and latency accounting.

Exit criteria:

- Candidate resolver strategies can be run, compared, and reported automatically.

## Phase 3: Strategy Search

- Implement failure mining.
- Implement `app.harness_optimizer.next_task`.
- Generate Codex tasks from eval and failure reports.
- Add configurable diarization/transcription reconciliation, speaker-name resolution, verification, retries, and voting.
- Add model-provider adapters.
- Add model transfer evaluation.
- Add failure clustering.

Exit criteria:

- The system can identify top failures and generate narrow implementation tasks with tests and eval commands.

## Phase 4: Media Providers

- Add local media ingestion.
- Add `ffmpeg` normalization.
- Add transcription and diarization provider interfaces.
- Add mocked provider tests.
- Add optional authorized YouTube caption access.

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
