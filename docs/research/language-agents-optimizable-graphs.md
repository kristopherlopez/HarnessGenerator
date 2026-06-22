# Language Agents As Optimizable Graphs

Last updated: 2026-06-02

Primary source: [Language Agents as Optimizable Graphs](https://arxiv.org/abs/2402.16823)

## Category

Graph-structured agent optimization.

## Core Idea

The paper models language-agent systems as graphs. Optimization can refine
node-level prompts and change graph connectivity.

## Why It Matters Here

Harnesses can be represented as graphs of steps: load context, call tools,
resolve identity, validate output, score failures, and decide next action.

## Implementation Notes

- Treat a harness as a graph of typed steps once config-only candidates are not
  enough.
- Optimize node config and edge routing separately.
- Keep graph changes auditable in candidate artifacts.
- Compare graph candidates against the same metrics and safety constraints as
  simpler strategies.

