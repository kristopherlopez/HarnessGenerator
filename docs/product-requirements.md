# Product Requirements

## Problem

Teams building AI agents often improve behavior through manual prompt edits, ad hoc retries, and one-off evaluation scripts. That makes improvements hard to reproduce and difficult to compare across models, datasets, and budgets.

HarnessGenerator should make harness design systematic. It should generate, evaluate, compare, and refine harnesses under controlled conditions.

## Users

- AI engineers evaluating agent or RAG workflows.
- Researchers studying test-time reasoning and harness optimization.
- Product teams that need measurable improvement without fine-tuning.
- Benchmark authors who need repeatable, auditable experiment runs.

## MVP

The MVP should support YouTube podcast speaker attribution end to end:

- Load podcast episodes from a JSONL manifest.
- Accept either an authorized YouTube caption/audio source or a local media file.
- Run a baseline transcription plus diarization harness.
- Resolve anonymous speaker labels to known speaker names when speaker metadata or reference samples are available.
- Capture prompts, outputs, tool calls, model costs, transcription costs, timings, and scores.
- Generate a candidate variation using an LLM proposer.
- Run the candidate under the same budget and scoring rules.
- Compare baseline vs candidate.
- Write a report and archive both harnesses.

## Functional Requirements

- Define task specs in a checked-in, versioned format.
- Support deterministic and LLM-judge scoring.
- Run each candidate with explicit token, cost, wall-clock, and retry limits.
- Preserve raw traces and derived summaries.
- Produce machine-readable and human-readable experiment reports.
- Support multiple model providers through adapters.
- Keep train, validation, and held-out test splits separate.
- Prevent candidate harnesses from reading hidden labels or evaluation answers.
- Produce timestamped speaker-attributed transcript artifacts in JSON and human-readable formats.
- Support scoring against human-labeled transcript segments.
- Track uncertain or conflicting speaker assignments for human review.

## Non-Functional Requirements

- Runs must be reproducible from a saved config.
- Candidate execution must be sandboxed before generated code is allowed.
- Metrics must include uncertainty where stochastic sampling is used.
- Provider credentials must never be written into traces or reports.
- The archive format should be easy to inspect with normal filesystem tools.

## Non-Goals

- Training or fine-tuning model weights.
- Claiming exact reproduction of Poetiq's private Meta-System.
- Optimizing directly against private benchmark leaderboards.
- Shipping an autonomous self-modifying system before the runner and evaluator are reliable.

## Success Metrics

- A candidate harness beats a naive baseline on validation data and retains lift on held-out data.
- The same harness runs across at least two model providers with minimal changes.
- Failed candidates produce enough evidence to explain why they failed.
- A new experiment can be rerun from archived config and source.
- Speaker attribution improves without materially worsening transcription quality or cost.
