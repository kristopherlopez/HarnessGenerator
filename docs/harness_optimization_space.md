# Harness Optimization Space

Poetiq's public descriptions emphasize optimizing the harness around a model: question strategy, sequential process, answer assembly, model routing, verification, and cost. This project encodes those levers in `bootstrap/harness_search_space.yaml` so recursive improvement has explicit boundaries.

## Change Surfaces

### Pipeline Structure

Controls how media and intermediate artifacts move through the system:

- chunking policy
- transcription before or after diarization
- second passes for uncertain spans
- episode-level reconciliation

### Evidence Strategy

Controls how identity evidence is generated and fused:

- voice-only matching
- face-only matching
- voice and face fusion
- active-speaker detection
- clustering before matching
- matching before clustering

### Thresholds And Policies

Controls when the harness resolves, rejects, or asks for review:

- assignment threshold
- review threshold
- unknown threshold
- top-candidate margin
- minimum voice duration
- face quality minimum

### Model And Tool Routing

Controls which provider or model handles each subtask:

- cheap route for easy spans
- stronger route for ambiguous spans
- local provider route
- API provider route
- transcription and diarization provider selection

### Prompt And Process Design

Controls LLM-facing reasoning steps:

- speaker-resolution prompt
- conflict explanation
- review summary
- episode-wide consistency checking
- segment-level reasoning

LLMs cannot be the only source of identity truth. They can explain, summarize, classify failures, generate tasks, or help map labels when non-LLM evidence exists.

### Verification

Controls post-processing checks:

- impossible speaker switches
- inconsistent identities
- missing provenance
- short utterance guard
- registry conflicts
- output contract compliance

### Budget Allocation

Controls where computation is spent:

- spend more on ambiguous spans
- stop early on high-confidence spans
- retry only recoverable failures
- cap review items
- enforce cost per media hour

## Staged Unlocks

The first loop may only change fixture-level resolver logic: thresholds, evidence strategy, and verification.

Media provider routing, real transcription/diarization pipelines, and generated code search come later, after contracts, evals, and regression gates are stable.

## Generated Task Requirements

Every generated improvement task must declare which change surface it modifies. This keeps recursion focused on auditable harness changes instead of broad rewrites.
