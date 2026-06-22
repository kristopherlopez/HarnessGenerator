# SWE-Agent

Last updated: 2026-06-02

Primary source: [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793)

## Category

Agent-computer interfaces for software engineering.

## Core Idea

SWE-agent shows that the interface between an agent and the computer environment
can materially affect software-engineering performance.

## Why It Matters Here

The harness generator is itself a software-engineering agent workflow. Edit
tools, repo navigation, test execution, and feedback presentation are part of
the harness, not incidental plumbing.

## Implementation Notes

- Keep commands non-interactive and reproducible.
- Prefer structured report artifacts over raw terminal scrollback.
- Make file edits, diffs, tests, and failure feedback easy for the optimizer to
  inspect.
- Treat the Codex workspace interface as part of the overall harness.

