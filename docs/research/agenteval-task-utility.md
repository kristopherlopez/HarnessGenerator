# AgentEval

Last updated: 2026-06-02

Primary source: [Assessing and Verifying Task Utility in LLM-Powered Applications](https://arxiv.org/abs/2405.02178)

## Category

Application utility evaluation.

## Core Idea

AgentEval proposes generating task-specific criteria to verify whether an
LLM-powered application is useful for its intended purpose.

## Why It Matters Here

The harness generator should not optimize generic model scores. It should
optimize workspace-specific utility: correct attribution, low false assignment,
clear provenance, bounded review load, and auditable failures.

## Implementation Notes

- Keep metric contracts close to workspace purpose.
- Distinguish user utility from internal proxy metrics.
- Add criteria for provenance and review ergonomics, not just identity accuracy.
- Use outcome artifacts to explain utility changes over time.

