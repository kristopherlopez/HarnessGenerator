# Evaluation Protocol

## Goal

The evaluation protocol exists to determine whether a harness change is a real improvement, a noisy result, or an overfit artifact.

## Splits

- `dev`: used for debugging and proposer context.
- `validation`: used during optimization and candidate selection.
- `test`: used only for final reporting.

Never allow generated harnesses to read test labels, private examples, or aggregate test feedback during optimization.

## Baselines

Every task family should include:

- Naive single-call baseline.
- Hand-written reasonable baseline.
- Best archived generated harness.
- Current candidate harness.

The current YouTube speaker-attribution workspace implements `baseline_unknown`,
`risky_top_candidate`, and `review_heavy_low_false_assignment`. Strategy comparison rejects high
raw identity accuracy when configured false-assignment or review-rate constraints are violated.

## Required Metrics

- Task score: exact match, pass rate, F1, judge score, or benchmark-specific score.
- Cost: provider cost estimate and token counts.
- Latency: wall-clock and model latency where available.
- Reliability: variance across repeated runs.
- Efficiency: number of model calls, tool calls, retries, and generated candidates.
- Constraint violations: timeout, memory, policy, unsafe tool use, malformed output.

The current fixture metrics include `identity_accuracy`, `false_assignment_rate`,
`known_person_precision`, `known_person_recall`, `unknown_detection_recall`,
`needs_review_rate`, `false_merge_rate`, `false_split_rate`, and
`latency_seconds_per_media_hour`. Cost and real latency accounting are still placeholders.

## Comparison Rules

- Use the same split, model, temperature, max tokens, and tool environment for baseline and candidate unless the experiment explicitly tests those factors.
- Repeat stochastic candidates enough times to estimate variance.
- Report confidence intervals or bootstrap intervals when practical.
- Prefer held-out performance over validation performance.
- Treat any candidate that uses more budget as a tradeoff, not a strict win, unless budget-weighted metrics improve.

## Overfitting Checks

- Compare validation lift against held-out lift.
- Run the same harness on at least one secondary model.
- Evaluate on adversarial or perturbed examples when available.
- Inspect whether the candidate memorized known examples or scoring quirks.
- Track performance by task bucket, not only aggregate score.

## Report Template

Use [templates/experiment-report.md](../templates/experiment-report.md) for each completed run.
