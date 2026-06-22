# AutoHarness

Last updated: 2026-06-02

Primary source: [AutoHarness: improving LLM agents by automatically synthesizing a code harness](https://arxiv.org/abs/2603.03329)

Related resource: [Snorkel AI reading group: Code World Models and AutoHarness for LLM Agents](https://snorkel.ai/blog/code-world-models-and-autoharness-for-llm-agents/)

## Category

Automatic code-harness synthesis.

## Core Idea

Google DeepMind's AutoHarness paper shows that an LLM can iteratively synthesize
code harnesses from environment feedback. In TextArena games, the synthesized
harness blocks illegal actions and can let a smaller model outperform larger
models by controlling the model-environment interface.

## Why It Matters Here

This is highly relevant to the harness generator. It demonstrates that
performance can improve by generating executable guardrails, legality checks,
and policy wrappers around a model without changing model weights.

## Implementation Notes

- Treat harness code/config as a first-class candidate artifact.
- Use environment or eval feedback to refine the harness.
- Add legality/safety checks before model output becomes an action.
- Preserve per-candidate failure evidence so the next code harness can target
  the actual failure mode.
- Start with constrained code/config generation before allowing broad policy
  synthesis.

