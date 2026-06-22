# Automated Design Of Agentic Systems

Last updated: 2026-06-02

Primary source: [Automated Design of Agentic Systems](https://arxiv.org/abs/2408.08435)

Related source: [OpenReview version](https://openreview.net/pdf?id=D01WR1yVW2)

## Category

Automated agent-system design.

## Core Idea

The paper proposes Automated Design of Agentic Systems, where a meta-agent
creates or combines agentic building blocks and evaluates the resulting systems
across tasks.

## Why It Matters Here

The harness generator is a narrower version of the same idea: search over
system design choices, score them, archive results, and feed evidence into the
next design step.

## Implementation Notes

- Define the design space before allowing broad candidate generation.
- Maintain an archive of candidate designs, outcomes, and discovered lessons.
- Separate mutation generation from evaluation and promotion.
- Prefer bounded config and workflow mutations before unrestricted code search.

