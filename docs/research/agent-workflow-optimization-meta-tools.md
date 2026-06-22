# Agent Workflow Optimization With Meta-Tools

Last updated: 2026-06-02

Primary source: [Optimizing Agentic Workflows using Meta-tools](https://arxiv.org/abs/2601.22037)

## Category

Tool-use and workflow efficiency optimization.

## Core Idea

The paper introduces Agent Workflow Optimization, a framework for identifying
and optimizing redundant tool-execution patterns in agentic workflows.

## Why It Matters Here

As the harness loop grows, waste can come from repeated evals, redundant report
generation, repeated provider calls, or unnecessary model/tool calls.

## Implementation Notes

- Record tool-call counts, model-call counts, latency, and cost in harness
  history.
- Add budget impact to candidate outcome artifacts.
- Let the optimizer propose workflow simplifications when quality is unchanged.
- Keep "same score, lower cost" as a separate promotion case from quality lift.

