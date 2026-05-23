# Workspaces And Boundaries

HarnessGenerator is the reusable engine. A workspace is a task-specific package of contracts,
datasets, harnesses, reports, and docs.

This split keeps engine concepts reusable while letting each task family define its own data,
metrics, safety rules, and workflows.

## Engine Responsibilities

The root project should provide generic machinery:

- contract loading
- workspace readiness checks
- adapter protocols
- eval entrypoints
- candidate comparison
- report writing
- safety and regression gates
- generated task structure

These pieces should not permanently assume one domain.

## Workspace Responsibilities

A workspace should provide task-specific pieces:

- task manifest
- input and output contracts
- safety contract
- metric contract
- dataset manifests
- baseline harness or strategy
- scorer and failure taxonomy
- allowed tools and provider policy
- workspace docs

An eval dataset alone is not enough. The workspace must also say how outputs are validated, how
candidates are compared, and which behaviors are unsafe.

## Current First Workspace

The first workspace is `workspaces/youtube_speaker_attribution`.

It exists to prove the loop on a difficult multimodal task: speaker-attributed transcription with
known speakers, unknown speakers, diarization, evidence provenance, confidence, and human review.

That workspace is an implementation target and benchmark, not the permanent boundary of the
HarnessGenerator engine.
