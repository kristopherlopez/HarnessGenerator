# Continual Harness

Last updated: 2026-06-02

Primary source: [Continual Harness: Online Adaptation for Self-Improving Foundation Agents](https://arxiv.org/abs/2605.09998)

## Category

Online adaptation and self-improving agents.

## Core Idea

The paper frames agent improvement as an online adaptation process where a
frozen foundation model improves through memory, strategy refinement, tool use,
and human-in-the-loop feedback.

## Why It Matters Here

The workspace loop already needs to improve over time as more gold data is
promoted. This paper is relevant to designing a memory/history system that
captures what each loop learned without requiring model fine-tuning.

## Implementation Notes

- Treat `experiments/harness_history.jsonl` as an evolving memory ledger.
- Record no-op and regressive candidates so the optimizer does not repeat them.
- Make human interventions explicit, especially gold promotions and label fixes.
- Keep online adaptation separate from gold truth; generated material is not
  promoted until review policy is satisfied.

