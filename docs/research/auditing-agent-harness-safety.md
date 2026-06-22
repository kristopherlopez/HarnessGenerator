# Auditing Agent Harness Safety

Last updated: 2026-06-02

Primary source: [Auditing Agent Harness Safety](https://arxiv.org/abs/2605.14271)

## Category

Harness safety and trajectory auditing.

## Core Idea

The paper argues that output-level evaluation can miss harness safety failures
that happen mid-trajectory, such as unauthorized resource access or incorrect
information flow between agents.

## Why It Matters Here

The repository already has non-negotiable safety rules around identity,
biometric artifacts, live APIs, and public API outputs. Those rules need
trajectory-level enforcement, not just final-output checks.

## Implementation Notes

- Audit tool/resource access during the run, not only final reports.
- Preserve permission boundaries in trace events.
- Add safety checks for generated harness candidates before promotion.
- Treat multi-agent expansion as a larger safety surface.

