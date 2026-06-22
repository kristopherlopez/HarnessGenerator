# AgentBench

Last updated: 2026-06-02

Primary source: [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688)

## Category

Agent benchmark and evaluation.

## Core Idea

AgentBench evaluates LLMs as agents across multiple interactive environments,
with emphasis on multi-turn reasoning and decision-making.

## Why It Matters Here

The project should evaluate complete task execution, not isolated model calls.
This matters for YouTube speaker attribution because the output depends on data
loading, provider artifacts, evidence selection, resolution policy, and review
workflow.

## Implementation Notes

- Evaluate end-to-end runs.
- Track environment and dataset versions with each report.
- Compare model/provider choices only when the harness and data snapshot are
  fixed.
- Keep benchmark results separate from promotion decisions unless the workspace
  policy says otherwise.

