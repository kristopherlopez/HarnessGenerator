# Multi-Agent Architecture Search Via Agentic Supernet

Last updated: 2026-06-02

Primary source: [Multi-agent Architecture Search via Agentic Supernet](https://arxiv.org/abs/2502.04180)

Related source: [OpenReview page](https://openreview.net/forum?id=imcyVlzpXh)

## Category

Multi-agent architecture search.

## Core Idea

The paper adapts architecture-search ideas to multi-agent systems, using an
agentic supernet as a search space for different agent configurations.

## Why It Matters Here

This is more relevant after the project has moved beyond single-run harness
configs. It suggests how to search across multi-agent decompositions when a task
needs separate reviewers, resolvers, validators, or planners.

## Implementation Notes

- Do not introduce multi-agent search until single-harness evals are stable.
- Use a small set of allowed agent roles before searching richer architectures.
- Track architecture cost, latency, and failure attribution alongside quality.
- Require safety constraints to hold at every agent boundary.

