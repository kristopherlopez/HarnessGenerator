# Why HarnessGenerator Exists

AI applications often fail because the system around the model is weak, not only because the model
is weak. Prompts, context selection, tool use, decomposition, verification, retries, stopping rules,
and output validation all shape the final behavior.

HarnessGenerator exists to make those system choices explicit and testable.

## The Problem

Many teams improve AI behavior through manual prompt edits and isolated experiments. That creates
several recurring problems:

- Changes are hard to compare because each run uses slightly different data or settings.
- Improvements can optimize a narrow sample while making safety worse.
- Failure analysis stays informal, so the next task is based on memory instead of evidence.
- Tool and provider choices drift without clear cost, latency, or reliability accounting.
- Public output contracts can change accidentally.

HarnessGenerator turns those choices into a controlled loop.

## The Project Goal

The project goal is to build a reusable engine that can:

- describe a task family with contracts and safety rules
- run baseline and candidate harnesses against datasets
- score outputs with task-specific metrics
- compare candidates under configured constraints
- preserve evidence about what happened
- generate narrow follow-up engineering tasks from observed failures

The engine should be reusable across task families. The first workspace is YouTube speaker
attribution, but the project is not intended to be only a speaker-attribution system.

## The Core Bet

The working hypothesis is:

> Many LLM failures are harness failures, not just model failures.

HarnessGenerator tests that hypothesis by improving the process around the model before assuming
that the only answer is fine-tuning or switching models.
