# Meta-Harness

Last updated: 2026-06-02

Primary source: [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/abs/2603.28052)

## Category

Harness optimization.

## Core Idea

The paper treats the harness around an LLM system as an optimization target. A
meta-system searches over harness code, using prior candidate source, scores,
and execution traces to generate improved harnesses.

## Why It Matters Here

This is one of the closest matches to the repository purpose. It supports the
idea that the outer loop should optimize code, prompts, context selection,
retrieval, tooling, and workflow rules rather than treating the model as the
only moving part.

## Implementation Notes

- Keep candidate harnesses as runnable artifacts, not only prose proposals.
- Preserve scores, traces, source snapshots, and failure notes for every run.
- Use held-out evals before promoting a candidate.
- Keep workspace-specific details out of the generic optimizer layer.

