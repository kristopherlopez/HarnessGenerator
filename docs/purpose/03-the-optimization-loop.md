# The Optimization Loop

HarnessGenerator is built around an outer loop that improves harnesses using eval evidence.

The loop is intentionally narrow. It should produce auditable changes, not uncontrolled
self-modification.

## Loop Shape

1. Load a workspace, contracts, dataset, and strategy.
2. Run the selected harness or strategy.
3. Validate and score the output.
4. Write reports and failure summaries.
5. Compare candidates against baselines and constraints.
6. Generate a narrow follow-up task from the highest-value failure.
7. Repeat only after the task is reviewed and implemented.

## What The Loop Optimizes

The loop can optimize more than accuracy:

- task score
- false-assignment or safety violation rate
- review burden
- malformed output rate
- cost
- latency
- tool-call count
- robustness across cases
- trace quality and debuggability

For high-risk tasks, a candidate with higher recall can still lose if it violates safety
constraints.

## What The Loop Should Not Do

The loop should not:

- expose hidden labels to candidate harnesses
- use live external APIs in tests
- change public schemas unless a task explicitly asks for it
- overwrite human-reviewed labels
- let LLM output become the only source of truth for high-risk facts
- generate broad code changes without a constrained task and regression checks

The point is controlled improvement, not automation without guardrails.
