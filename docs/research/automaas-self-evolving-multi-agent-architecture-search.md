# AutoMaAS

Last updated: 2026-06-02

Primary source: [AutoMaAS: Self-Evolving Multi-Agent Architecture Search for Large Language Models](https://arxiv.org/abs/2510.02669)

## Category

Self-evolving multi-agent architecture search.

## Core Idea

AutoMaAS searches for multi-agent configurations and evolves operators over
time, borrowing ideas from neural architecture search and automated machine
learning.

## Why It Matters Here

The useful connection is operator lifecycle management: proposed mutation
operators should be born, evaluated, reused, revised, or retired based on their
observed effects.

## Implementation Notes

- Store operator provenance in candidate reports.
- Track whether each operator tends to create no-ops, improvements, or
  regressions.
- Retire mutation surfaces that repeatedly fail on the current task family.
- Keep operator evolution constrained by workspace safety rules.

