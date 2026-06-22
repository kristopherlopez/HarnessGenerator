# A2Flow

Last updated: 2026-06-02

Primary source: [A^2Flow: Automating Agentic Workflow Generation via Self-Adaptive Abstraction Operators](https://arxiv.org/abs/2511.20693)

## Category

Workflow abstraction and operator search.

## Core Idea

A2Flow extends workflow generation by extracting reusable abstraction operators
from cases and applying them as self-adaptive workflow building blocks.

## Why It Matters Here

The harness generator will need reusable mutation operators: threshold tuning,
review escalation, evidence routing, trace compression, retry changes, and
provider-routing changes.

## Implementation Notes

- Treat proposal templates as early mutation operators.
- Record which operator produced each candidate.
- Measure operator-level success rates over time.
- Promote reusable operators only when they repeatedly improve held-out evals.

