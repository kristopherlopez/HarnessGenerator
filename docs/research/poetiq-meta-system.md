# Poetiq Meta-System

Last updated: 2026-06-02

Primary source: [Recursive Self-Improvement Delivers New State-of-the-Art Coding Performance](https://poetiq.ai/posts/recursive_self_improvement_coding/)

Related source: [Traversing the Frontier of Superintelligence](https://poetiq.ai/posts/arcagi_announcement/)

Related source: [Poetiq Featured on YC Root Access](https://outsetcapital.com/blog/poetiq-yc-root-access)

## Category

Recursive harness construction and model-agnostic orchestration.

## Core Idea

Poetiq publicly describes a Meta-System that automatically builds and optimizes
task-specific harnesses around standard API models. Their coding-benchmark
writeup claims the system built a LiveCodeBench Pro harness from scratch,
optimized for Gemini 3.1 Pro, then transferred that same harness to other
models.

## Why It Matters Here

This is conceptually close to this repository's objective: a meta-system that
generates task-family harnesses, evaluates them, and improves the harness rather
than fine-tuning the base model.

## Implementation Notes

- Track whether a learned harness transfers across models/providers.
- Optimize for multiple constraints at once: accuracy, runtime, memory, cost,
  review burden, and safety.
- Keep model-specific behavior separate from reusable harness behavior.
- Treat Poetiq's claims as public company reports, not independently
  reproducible research unless artifacts are released.

