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

## Required Metrics

- Task score: exact match, pass rate, F1, judge score, or benchmark-specific score.
- Cost: provider cost estimate and token counts.
- Latency: wall-clock and model latency where available.
- Reliability: variance across repeated runs.
- Efficiency: number of model calls, tool calls, retries, and generated candidates.
- Constraint violations: timeout, memory, policy, unsafe tool use, malformed output.

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

Use [templates/experiment-report.md](templates/experiment-report.md) for each completed run.

