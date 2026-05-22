# Project Boundaries

HarnessGenerator is the reusable engine. YouTube speaker attribution is the first workspace and MVP benchmark.

This distinction matters because the harness generator should not start optimizing a task until the workspace has enough structure to run, score, compare, and audit candidates safely.

## Generic HarnessGenerator Responsibilities

The reusable engine should provide:

- workspace discovery and path resolution
- contract loading and validation
- readiness validation before optimization
- dataset adapter interfaces
- harness or strategy registration interfaces
- output validation before scoring
- eval execution under budget limits
- trace, report, and archive writing
- failure mining interfaces
- bounded candidate proposal and Codex task generation
- provider and tool policy enforcement
- regression and safety gates

These concepts should work for any task family that supplies the required workspace pieces.

## First Workspace Responsibilities

The current first workspace is `workspaces/youtube_speaker_attribution`. It owns the YouTube speaker-attribution task family:

- audio, video, and caption-style inputs
- transcript, diarization, and speaker identity outputs
- known and unknown speaker handling
- identity evidence and provenance requirements
- false-assignment, false-merge, false-split, and review metrics
- transcription, diarization, face, voice, and LLM tool policy
- resolver strategies such as `baseline_unknown` and `review_heavy_low_false_assignment`
- speaker-attribution datasets, fixtures, reports, harnesses, and generated tasks

The current implementation is intentionally seeded around this workspace. Future work should keep it working while extracting generic interfaces from the first task-specific implementation.

## Currently Mixed Areas

Some root-level files are reusable in shape but still encode first-workspace assumptions:

| Area | Current State | Target State |
| --- | --- | --- |
| `bootstrap/*.yaml` | Includes speaker-attribution defaults such as identity policy and false-assignment metrics | Generic defaults plus workspace-specific overrides |
| `app.identity` | Contains the runnable first-workspace models and strategies | Wrapped by a YouTube task adapter |
| `evals.dataset` | Loads `app.identity.models.EvalCase` | Calls a workspace dataset adapter |
| `evals.metrics` | Scores identity-resolution predictions | Calls a workspace scorer |
| `evals.run_eval` | Imports identity strategies directly | Runs a selected workspace adapter |
| `evals.compare_strategies` | Compares identity strategies directly | Compares registered workspace harnesses or strategies |
| `app.harness_optimizer.candidates` | Uses speaker-attribution proposal templates | Gets templates from a workspace candidate provider |
| Root `AGENTS.md` | Contains speaker-attribution safety rules | Generic repo rules at root; task-specific rules under the workspace |

## What A Workspace Must Provide

An evaluation set alone is not enough. A workspace must provide:

- `task.yaml` with workspace id, task family, default dataset, default baseline or strategy, and path declarations
- contracts for input, output, metrics, safety, datasets, tools, strategy space, harness search space, and generated-task policy
- dataset manifests and split policy for development, validation, test, regression, and private or hidden-label data where applicable
- at least one tiny labelled fixture that can run quickly in tests
- a safe baseline harness or strategy
- a scorer that produces the primary metric and configured secondary metrics
- output validation that runs before scoring
- failure categories and failure-mining logic
- allowed harness change surfaces for candidate generation
- model/provider/tool policy, including network, filesystem, cache, and live-API rules
- budget limits for cost, calls, tokens, retries, and wall-clock time
- report and archive paths for runs, traces, scores, failures, and generated tasks
- readiness validation proving the workspace can run a baseline before optimization starts

## Generic Vs Workspace-Specific Map

| Part | Generic Engine | Workspace-Specific |
| --- | --- | --- |
| Contracts | Loading, override behavior, common validation, required file discovery | Task schema fields, safety rules, allowed tools, metric names, change surfaces |
| Datasets | Manifest discovery, split policy checks, hidden-label protections | Case schema, fixture content, labels, task-specific loaders |
| Harnesses | Registration, execution protocol, candidate archive | Baseline logic, task-specific strategies, prompts, tool routing |
| Eval runner | Run orchestration, budget enforcement, report writing | Task instance execution, output validation, scoring |
| Metrics | Metric contract shape, comparison and constraint enforcement | Metric implementations and task-specific pass/fail meaning |
| Failure mining | Failure report shape and task-generation handoff | Failure taxonomy, suspected-cause logic, priority ordering |
| Candidate generation | Proposal schema, policy checks, generated-task rendering | Candidate templates, expected metric effects, risk notes |
| Provider/tool policy | Permission model, mocks, tracing, secret redaction | Concrete provider interfaces and task-specific tool capabilities |
| Readiness | Stage model, blocking behavior, report format | Workspace-specific readiness checks and minimum fixture expectations |

## Documentation Ownership

Generic project docs should describe reusable engine concepts:

- `README.md`
- `docs/architecture.md`
- `docs/product-requirements.md`
- `docs/workspace_layout.md`
- `docs/data_contracts.md`
- `docs/evaluation-protocol.md`
- `docs/security-and-safety.md`
- `docs/codex_workflow.md`
- `docs/project_boundaries.md`
- `docs/to-do/*`

These current root docs are specific to the YouTube speaker-attribution workspace and should eventually move under `workspaces/youtube_speaker_attribution/docs/` or be clearly kept as first-workspace examples:

- `docs/task-family-youtube-speaker-attribution.md`
- `docs/resolver_strategies.md`
- `docs/failure_modes.md`
- `docs/registry_design.md`

## Glossary

- **Workspace:** A self-contained task-family directory under `workspaces/<workspace_id>/` with contracts, datasets, harnesses, reports, runs, and generated tasks.
- **Task family:** A class of problems with a shared input schema, output schema, scoring method, safety policy, and optimization surface.
- **Task adapter:** The code boundary that lets the generic runner load a workspace's cases, run harnesses, validate outputs, score results, mine failures, and provide candidate templates.
- **Candidate harness:** A runnable task-solving process being evaluated against a baseline, such as a prompt/config strategy or restricted code implementation.
- **Baseline harness:** The simplest safe runnable harness used to establish a reproducible starting score.
- **Eval split:** A named dataset partition such as `dev`, `validation`, `test`, `regression`, or `private`.
- **Hidden labels:** Ground-truth labels or private examples that scorers may use but candidate harnesses and proposer prompts must not read.
- **Failure miner:** A task-specific analyzer that turns scored outputs into failure types, affected cases, suspected causes, and improvement opportunities.
- **Change surface:** A bounded area the optimizer is allowed to modify, such as thresholds, verification, prompt process, tool routing, retry policy, or budget allocation.
