# LLM Readiness Harness

Last updated: 2026-06-02

Primary source: [LLM Readiness Harness: Evaluation, Observability, and CI Gates for LLM/RAG Applications](https://arxiv.org/abs/2603.27355)

## Category

Evaluation, observability, and CI gates.

## Core Idea

The paper frames readiness as an evidence-gated process involving evaluation,
observability, and CI-style promotion checks for LLM and RAG systems.

## Why It Matters Here

This aligns with the repository's definition of done: tests, lint, type checks,
eval reports, regression checks, and contract preservation before promotion.

## Implementation Notes

- Keep readiness checks explicit and runnable from the CLI.
- Store readiness reports as generated artifacts.
- Gate harness promotion on metric deltas and safety constraints.
- Treat synthetic data as useful but separate from reviewed gold.

