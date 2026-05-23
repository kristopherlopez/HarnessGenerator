# What A Harness Is

A harness is the runnable process that turns one task input into one task output.

It can be simple, such as a baseline strategy that always returns `unknown`, or complex, such as a
multi-step process that calls models, routes tools, verifies outputs, and asks for human review when
evidence is weak.

## A Harness Can Include

- input normalization
- context selection
- prompt templates
- model routing
- tool calls
- decomposition into substeps
- candidate generation
- verification
- confidence thresholds
- retry and stopping rules
- output validation
- review routing

HarnessGenerator treats these as change surfaces. A candidate harness should declare what it
changes so the project can evaluate whether that change helped.

## Harnesses Are Not Just Prompts

Prompt text is one part of a harness, but it is not the whole system. A useful harness also defines:

- what evidence can be used
- which tools are allowed
- how outputs are checked
- which failures are disqualifying
- when the system should abstain
- how cost and latency are bounded

This matters because a better prompt can still be unsafe if it ignores evidence provenance, leaks
hidden labels, or changes public output shape.

## Baselines And Candidates

A baseline harness is the safe reference point. It should be reproducible and intentionally simple.

A candidate harness is a proposed improvement. It must be compared against the baseline on the same
dataset, under the same contracts, unless the experiment explicitly changes those conditions.

The project prefers conservative, measurable improvements over broad rewrites.
