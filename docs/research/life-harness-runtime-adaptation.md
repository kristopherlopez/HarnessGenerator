# Life-Harness

Last updated: 2026-06-02

Primary source: [Adapting the Interface, Not the Model: Runtime Harness Adaptation for Deterministic LLM Agents](https://arxiv.org/abs/2605.22166)

## Category

Runtime harness adaptation.

## Core Idea

Life-Harness adapts the runtime interface around frozen LLM agents. It converts
recurring trajectory failures into reusable interventions across environment
contracts, procedural skills, action realization, and trajectory regulation.

## Why It Matters Here

This reinforces a central design choice: the harness can improve through
environment-side structure even when model weights and evaluation conditions
remain fixed.

## Implementation Notes

- Mine repeated failures from `harness_history.jsonl`.
- Convert repeated failure patterns into reusable harness interventions.
- Keep interventions fixed during held-out evaluation.
- Measure transfer across strategies/models to separate reusable harness logic
  from model-specific tuning.

