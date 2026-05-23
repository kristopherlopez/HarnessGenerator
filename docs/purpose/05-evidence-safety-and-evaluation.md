# Evidence, Safety, And Evaluation

HarnessGenerator is useful only if improvements are trustworthy. That requires evidence,
contracts, and repeatable evaluation.

## Evidence First

Candidates should not make important claims without provenance. For identity-style tasks, that
means a real-person assignment must be backed by evidence such as reviewed labels, provider output,
reference matches, or other configured signals.

The general rule is:

- prefer abstention over unsupported certainty
- preserve provenance for every important decision
- keep sensitive internals out of public outputs
- route ambiguous cases to review when the contract requires it

## Contracts Protect The Task

Contracts define what a workspace allows:

- input shape
- output shape
- metric names and constraints
- safety rules
- tool and provider policy
- candidate change surfaces
- generated task requirements

When contracts are machine-readable, the harness loop can reject unsafe or malformed candidates
before they are treated as improvements.

## Evaluation Makes Improvement Real

An improvement is only meaningful when it is measured under stable conditions.

A useful eval should answer:

- Did task quality improve?
- Did safety regress?
- Did review burden change?
- Did cost or latency change?
- Which failures remain?
- Is the result likely to generalize beyond the current fixture?

The project definition of done should include tests, lint, type checks, relevant evals, regression
checks, and documentation updates when behavior or contracts change.
