# AGENTS.md

## Project Purpose

This repository builds a multimodal identity-resolution harness for speaker-attributed transcription.

The system accepts audio/video and returns transcript segments with:

- diarization speaker labels
- resolved real-person identity where evidence is strong
- unknown speaker labels where identity is not known
- confidence scores
- evidence summaries
- human-review flags

The domain includes approximately 200-300 known speakers.

## Non-Negotiable Rules

- Prefer `unknown` or `needs_review` over wrong real-person attribution.
- Do not make identity assignments without evidence provenance.
- Do not expose raw face embeddings, voice embeddings, face crops, or raw frames through public API responses.
- Do not overwrite human-reviewed labels.
- Do not allow LLM calls to be the only source of identity truth.
- Do not change public API schemas unless the task explicitly asks for it.
- Do not modify safety contracts unless the task explicitly asks for it.
- Do not use live external APIs in tests.
- Do not add resolver logic without tests and eval output.
- Do not hardcode thresholds without adding them to config and docs.

## Commands

Install:

```powershell
uv sync
```

Run tests:

```powershell
uv run pytest
```

Run lint:

```powershell
uv run ruff check .
```

Run type checks:

```powershell
uv run mypy app evals
```

Run evals:

```powershell
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

Validate bootstrap contracts:

```powershell
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
```

Compare strategies:

```powershell
uv run python -m evals.compare_strategies --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

Check regressions:

```powershell
uv run python -m evals.check_regression --workspace workspaces/youtube_speaker_attribution
```

Generate next Codex task:

```powershell
uv run python -m app.harness_optimizer.next_task --workspace workspaces/youtube_speaker_attribution
```

Generate candidate harness changes:

```powershell
uv run python -m app.harness_optimizer.candidates --workspace workspaces/youtube_speaker_attribution
```

## Definition of Done

A change is done only when:

- tests pass
- lint passes
- relevant evals run
- identity logic changes include regression tests
- eval report shows before/after metric impact
- public API contract is preserved unless explicitly changed
- biometric safety rules are preserved
- docs are updated when contracts or resolver behavior changes

## Review Focus

When reviewing PRs, flag:

- false-assignment risk
- false-merge risk
- identity decisions without provenance
- missing open-set unknown handling
- public exposure of biometric internals
- missing regression tests
- metric gaming, especially improving recall while increasing false assignments
