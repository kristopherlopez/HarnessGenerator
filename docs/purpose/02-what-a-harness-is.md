# What A Harness Is

A harness is the runnable process that turns one task input into one task output.

It can be simple, such as a baseline strategy that always returns `unknown`, or complex, such as a
multi-step process that calls models, routes tools, verifies outputs, and asks for human review when
evidence is weak.

The Harness API is not the task output. The API is the execution boundary that lets
HarnessGenerator run a proposed harness, capture what happened, and compare the harness output to
gold data in a consistent way.

## The Core Loop

HarnessGenerator is built around this artifact flow:

```text
task inputs + gold outputs
        |
        v
generator proposes a harness hypothesis
        |
        v
runner executes that harness through the Harness API
        |
        v
harness produces predicted task outputs plus run metadata
        |
        v
evaluator compares predictions to gold outputs
        |
        v
failure analysis and optimizer decision
        |
        v
generator proposes a revised harness hypothesis
```

The harness is the generated or hand-authored process inside that loop. The task output is only one
artifact produced by running the harness.

## Key Artifacts

- **Task input:** One case supplied by a workspace, such as a question, transcript fixture, media
  excerpt, code task, or retrieval query.
- **Gold output:** The reviewed expected answer or label used by the evaluator. Candidate harnesses
  must not read hidden gold outputs.
- **Predicted task output:** The answer produced by a harness for one task input.
- **Harness hypothesis:** The proposed process for producing outputs, including prompts, model
  routing, tool policy, verification, retries, stopping rules, and confidence or abstention policy.
- **Harness API:** The stable execution boundary, conceptually `run(case, context) -> result`, used
  by the runner to execute any candidate harness safely.
- **Harness run result:** The predicted output plus trace metadata, validation status, cost,
  latency, retries, tool calls, model calls, and errors.
- **Evaluation output:** Metrics, diffs against gold, per-case failures, constraint violations, and
  aggregate scorecards.
- **Optimizer output:** The accept/reject decision, rationale, next proposed harness change, or a
  generated Codex task.

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

## What The Harness API Should Provide

The current code has a small `HarnessStrategy` shape for early fixtures. A fuller Harness API should
eventually provide:

- a stable `run(case, context)` entrypoint
- declared harness metadata, version, and supported contract versions
- structured configuration snapshot
- allowed tool and provider handles through the run context
- budget and timeout enforcement hooks
- trace events for model calls, tool calls, retries, validation, and errors
- output-contract and safety-contract validation hooks
- reproducibility metadata for archiving and comparison

That API is what makes it possible for the outer loop to generate, run, compare, and revise harness
hypotheses without each workspace inventing a different execution shape.
