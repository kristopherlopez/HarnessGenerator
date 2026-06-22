# AFlow

Last updated: 2026-06-02

Primary source: [AFlow: Automating Agentic Workflow Generation](https://arxiv.org/abs/2410.10762)

## Category

Agentic workflow generation.

## Core Idea

AFlow automates the generation and optimization of agentic workflows instead of
requiring humans to manually design every workflow structure.

## Why It Matters Here

The named workspace loops are currently hand-authored. AFlow is relevant to the
next stage: proposing workflow changes, not just resolver-threshold changes.

## Implementation Notes

- Represent loops as structured data in `task.yaml`, not only docs.
- Allow the optimizer to propose changes to workflow order, stopping rules, and
  verification steps.
- Score workflow changes with the same baseline/candidate comparison mechanism.
- Track whether a workflow change improves quality, cost, latency, or review
  burden.

