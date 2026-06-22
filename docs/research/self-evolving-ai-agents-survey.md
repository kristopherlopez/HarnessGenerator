# Survey Of Self-Evolving AI Agents

Last updated: 2026-06-02

Primary source: [A Comprehensive Survey of Self-Evolving AI Agents: A New Paradigm Bridging Foundation Models and Lifelong Agentic Systems](https://arxiv.org/abs/2508.07407)

## Category

Survey and taxonomy.

## Core Idea

The survey organizes research on agents that improve from interaction data,
environmental feedback, memory, tool use, and self-refinement rather than
remaining static after deployment.

## Why It Matters Here

This is a useful map for deciding which self-improvement mechanisms are mature
enough to implement and which should remain future work.

## Implementation Notes

- Use the survey to classify improvement mechanisms before expanding scope.
- Keep separate ledgers for data evolution, prompt/config evolution, tool
  evolution, and workflow evolution.
- Require explicit eval evidence for any claimed self-improvement.
- Treat safety, rollback, and auditability as first-order design constraints.

