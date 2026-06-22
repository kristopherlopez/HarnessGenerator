# Shepherd

Last updated: 2026-06-02

Primary source: [Shepherd: A Runtime Substrate Empowering Meta-Agents with a Formalized Execution Trace](https://arxiv.org/abs/2605.10913)

## Category

Runtime substrate and execution trace.

## Core Idea

Shepherd treats an agent execution as a structured object that meta-agents can
inspect, fork, replay, and transform. Model calls, tool calls, and environment
changes become events in a Git-like trace.

## Why It Matters Here

Harness optimization needs better trace semantics than plain logs. If a
candidate fails, the optimizer should be able to inspect the exact state, fork
from a meaningful point, and test a targeted change.

## Implementation Notes

- Keep trace events structured and machine-readable.
- Preserve model calls, tool calls, environment changes, and eval results.
- Consider fork/replay support once loop execution becomes expensive.
- Use trace structure for failure attribution and next-candidate generation.

