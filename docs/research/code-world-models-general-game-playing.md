# Code World Models

Last updated: 2026-06-02

Primary source: [Code World Models for General Game Playing](https://arxiv.org/abs/2510.04542)

Related resource: [Snorkel AI reading group: Code World Models and AutoHarness for LLM Agents](https://snorkel.ai/blog/code-world-models-and-autoharness-for-llm-agents/)

## Category

Executable world-model synthesis.

## Core Idea

The paper uses LLMs to translate game rules and trajectories into executable
Python world models. Classical planners such as MCTS can then reason over the
generated model instead of asking the LLM to directly choose actions.

## Why It Matters Here

The harness-generator analogue is to shift work from stochastic model calls into
deterministic code where possible. If a task rule can be expressed as executable
logic, the harness should prefer that over repeated natural-language reasoning.

## Implementation Notes

- Convert stable task rules into code or config validators.
- Use tests derived from trajectories/gold cases to refine generated logic.
- Separate model-generated evidence from deterministic verification.
- Prefer planner/verifier components when they can reduce model calls and
  illegal actions.

