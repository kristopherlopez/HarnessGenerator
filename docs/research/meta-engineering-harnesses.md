# Meta-Engineering Harnesses

Last updated: 2026-06-02

Primary source: [Meta-Engineering Harnesses for AI-Native Software Production](https://arxiv.org/abs/2605.25665)

## Category

Contract-driven production harnesses.

## Core Idea

The paper presents a software-production harness that turns requirements into
contracts, routes work through role-specialized agents, performs independent and
adversarial verification, and improves through structured failure classification
and outer-loop calibration.

## Why It Matters Here

This matches several repository design choices: contracts, workspace-level
promotion policy, failure classification, independent verification, and
longitudinal harness history.

## Implementation Notes

- Keep contracts explicit before generating candidate changes.
- Use independent verification paths where identity or safety risk is high.
- Treat failure classification as input to the next loop.
- Preserve deployment-like readiness criteria even for local workspace loops.

