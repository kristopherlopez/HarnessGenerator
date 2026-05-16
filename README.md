# HarnessGenerator

HarnessGenerator is a planned framework for automatically designing, evaluating, and improving AI task harnesses. The goal is to build a practical, open implementation of a "meta-system" style workflow: given a task family, examples, constraints, and evaluation data, the system proposes candidate harnesses, runs them, scores them, studies failures, and iterates toward a better task-specific agent wrapper.

This project is inspired by Poetiq's public descriptions of its Meta-System, but it is not affiliated with Poetiq and should not be treated as a reproduction of their private implementation.

## Why This Exists

Poetiq's public writing argues that model performance depends heavily on the system wrapped around the model: what questions are asked, which intermediate artifacts are created, how candidate answers are checked, how tools are used, and when the process stops. Their recent benchmark posts describe automatically created harnesses that improve multiple underlying models without fine-tuning or privileged model access.

The working hypothesis for this project is:

> Many LLM failures are harness failures, not just model failures.

HarnessGenerator exists to test that hypothesis by turning harness design into a repeatable optimization problem.

## Target Outcome

The intended system should be able to:

- Accept a task specification, dataset split, model provider config, budget, and scoring function.
- Generate candidate harness implementations from a constrained template or plugin API.
- Execute candidates in a sandboxed runner with full trace capture.
- Score candidates on quality, cost, latency, token usage, robustness, and safety constraints.
- Feed traces and failure summaries back into an outer-loop proposer.
- Maintain an archive of prior candidates, scores, design notes, and reusable strategies.
- Export the best harness as code plus an auditable report.
- Generate narrow Codex tasks from failure reports instead of directly self-modifying production code.

## Poetiq-Inspired Principles

Public sources suggest several design principles worth adopting:

- **Build on top of models, not into them.** Optimize orchestration, context, verification, and tool use before attempting model training.
- **Keep the harness model-agnostic.** A harness should run across providers when possible so improvements are not tied to one model.
- **Search over process, not only prompts.** Candidate harnesses can change decomposition, context selection, tool policy, verification, retries, ensembles, and stopping rules.
- **Use recursive improvement carefully.** Each run should create evidence that helps the next run, not just free-form self-reflection.
- **Score against constraints.** Accuracy alone is incomplete; cost, runtime, memory, and reliability matter.
- **Preserve traces.** The system should be debuggable, reproducible, and auditable.

## Planned Architecture

```text
Task Spec
   |
   v
Dataset Adapter ----> Evaluation Runner ----> Metrics + Traces
   |                         ^                       |
   v                         |                       v
Harness Template API ---> Candidate Harness ---> Failure Analysis
   ^                                                 |
   |                                                 v
Candidate Archive <----- Outer-Loop Proposer <--- Research Memory
```

Core modules will be organized around:

- `bootstrap`: machine-readable contracts for domain, tools, metrics, safety, and task generation.
- `spec`: task and benchmark definitions.
- `harness`: interfaces for generated harnesses.
- `runner`: sandboxed execution, retries, limits, and trace capture.
- `eval`: metrics, judges, validators, and statistical comparison.
- `optimizer`: candidate proposal, mutation, selection, and archive policy.
- `reports`: experiment summaries and exportable harness cards.
- `workspaces/*/codex_tasks`: generated PR-sized engineering tasks for each task family.

## Initial Use Cases

The first benchmark family is YouTube podcast speaker attribution:

- Input: a YouTube podcast URL or locally provided audio/video asset.
- Output: a timestamped transcript with accurate speaker labels.
- Core challenge: combine transcription, diarization, speaker-name resolution, and confidence-aware correction.
- Primary metric: speaker-attribution accuracy against a human-labeled reference transcript.
- Secondary metrics: word error rate, diarization error rate, segment boundary quality, cost, latency, and manual-review burden.

See [docs/task-family-youtube-speaker-attribution.md](docs/task-family-youtube-speaker-attribution.md) for the benchmark design.

## Repository Map

```text
.
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── bootstrap/
│   ├── codex_task_policy.yaml
│   ├── dataset_manifest.yaml
│   ├── domain_contract.yaml
│   ├── harness_search_space.yaml
│   ├── input_contract.yaml
│   ├── metric_contract.yaml
│   ├── output_contract.yaml
│   ├── safety_contract.yaml
│   ├── strategy_space.yaml
│   └── tool_registry.yaml
├── docs/
│   ├── architecture.md
│   ├── codex_workflow.md
│   ├── data_contracts.md
│   ├── evaluation-protocol.md
│   ├── failure_modes.md
│   ├── harness_optimization_space.md
│   ├── product-requirements.md
│   ├── research-notes.md
│   ├── registry_design.md
│   ├── resolver_strategies.md
│   ├── roadmap.md
│   ├── security-and-safety.md
│   ├── task-family-youtube-speaker-attribution.md
│   ├── workspace_layout.md
│   └── templates/
│       ├── experiment-report.md
│       ├── harness-spec.yaml
│       └── youtube-speaker-attribution-spec.yaml
├── workspaces/
│   └── youtube_speaker_attribution/
│       ├── task.yaml
│       ├── intake/
│       ├── contracts/
│       ├── datasets/
│       ├── harnesses/
│       ├── experiments/
│       ├── runs/
│       ├── codex_tasks/
│       └── reports/
└── .gitignore
```

## Implementation Status

This repository currently contains the first runnable bootstrap loop:

- bootstrap YAML contract loading and validation
- synthetic labelled identity-resolution fixtures
- baseline, risky, and conservative resolver strategies
- eval report and failure report generation
- strategy comparison under safety constraints
- machine-readable harness optimization surfaces
- regression checks
- generated Codex task output
- workspace-first organization for task-specific artifacts

It does not yet ingest real YouTube, audio, or video media.

## Quick Start

Install dependencies:

```powershell
uv sync
```

Run tests, lint, and type checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy app evals
```

Run the first recursive harness cycle:

```powershell
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
uv run python -m evals.compare_strategies --workspace workspaces/youtube_speaker_attribution --dataset small_gold
uv run python -m evals.check_regression --workspace workspaces/youtube_speaker_attribution
uv run python -m app.harness_optimizer.candidates --workspace workspaces/youtube_speaker_attribution
uv run python -m app.harness_optimizer.next_task --workspace workspaces/youtube_speaker_attribution
```

## Suggested Build Order

1. Build the bootstrap contract loader and validation tests.
2. Build a labelled fixture eval runner for identity-resolution strategies.
3. Compare `baseline_unknown` against one conservative resolver under the metric contract.
4. Add failure mining and generated Codex tasks.
5. Add trace capture and experiment reports.
6. Add real media ingestion and provider adapters behind mocked tests.
7. Expand the search space to resolver strategies, threshold search, verification, and model routing.

The harness change surfaces are defined in
[docs/harness_optimization_space.md](docs/harness_optimization_space.md) and
`bootstrap/harness_search_space.yaml`.

The workspace-first layout is described in
[docs/workspace_layout.md](docs/workspace_layout.md).

Gold dataset output for speaker attribution is described in
`workspaces/youtube_speaker_attribution/docs/gold_dataset_output.md`.

Starting from YouTube links without gold labels is described in
`workspaces/youtube_speaker_attribution/docs/bootstrapping_without_gold.md`.

## Research Sources

See [docs/research-notes.md](docs/research-notes.md) for the research summary and source links used to shape this plan.
