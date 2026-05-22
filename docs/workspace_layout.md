# Workspace Layout

HarnessGenerator uses a workspace-first layout. Reusable meta-system code stays at the repo root; task-specific artifacts live under `workspaces/<workspace_id>/`.

## Root-Level Engine

```text
app/        reusable engine modules plus current first-workspace implementation code
bootstrap/  global default contracts and first-workspace-seeded defaults to extract
evals/      reusable eval entrypoints plus current first-workspace scorer glue
docs/       project-level documentation and first-workspace docs pending relocation
tests/      engine and workspace behavior tests
```

Root code should move toward generic contracts, adapters, runners, optimizers, reports, and safety gates. Current identity-resolution modules are part of the first runnable workspace implementation until they are wrapped by a task adapter.

## Task Workspace

```text
workspaces/youtube_speaker_attribution/
├── task.yaml
├── intake/
├── contracts/
├── datasets/
├── harnesses/
├── experiments/
├── runs/
├── codex_tasks/
└── reports/
```

`task.yaml` is the workspace manifest. It names the task family and declares where its contracts, datasets, harnesses, runs, experiments, generated tasks, and reports live.

`intake/` stores raw source links and notes before they become dataset cases.

`contracts/` contains task-specific overrides for global defaults. The loader reads `bootstrap/` first, then applies matching workspace contract files.

`datasets/` contains labelled fixtures and future train, validation, test, regression, and adversarial sets. Use `datasets/drafts/` for partial annotations and `datasets/small_gold/` only for reviewed ground truth.

`harnesses/` contains promoted, reviewable harnesses. Failed or temporary candidates should stay in `runs/` or `experiments/` unless promoted.

`experiments/` will contain ablation plans and comparison reports.

`runs/` is for immutable run evidence: harness snapshots, metrics, failures, traces, and reports.

`codex_tasks/` contains generated task templates and candidate implementation tasks.

`reports/` contains latest eval, failure, strategy-comparison, readiness, and candidate-proposal reports.

## Workspace Requirements

A workspace needs more than an evaluation set before HarnessGenerator should optimize it. It must provide:

- `task.yaml` with workspace id, task family, default dataset, default baseline or strategy, and paths
- task-specific contracts for input, output, metrics, safety, datasets, tools, strategy space, harness search space, and generated-task policy
- dataset manifests and split policy
- at least one tiny labelled fixture
- a safe baseline harness or strategy
- output validation before scoring
- scoring logic for the primary metric and constraints
- failure categories and failure-mining logic
- allowed change surfaces for candidate generation
- explicit model, provider, tool, network, filesystem, and live-API policy
- budget limits and report/archive locations
- a readiness report proving the baseline can run

Until those pieces exist, candidate generation should be blocked.

## Generic Vs Workspace-Specific

| Part | Generic Engine | Workspace-Specific |
| --- | --- | --- |
| Contracts | Loading, override behavior, common validation | Task schema fields, safety rules, metric names |
| Datasets | Manifest and split checks | Case schema, fixture content, labels |
| Harnesses | Registration and execution protocol | Baselines, prompts, strategies, tool routing |
| Eval runner | Orchestration, budget checks, report writing | Output validation and metric implementation |
| Failure mining | Failure report handoff | Failure taxonomy and suspected causes |
| Candidate generation | Proposal schema and policy checks | Candidate templates and risk notes |
| Provider policy | Permissions, mocks, redaction | Concrete tool capabilities |

See [project_boundaries.md](project_boundaries.md) for the full boundary map and glossary.

## Command Pattern

Every task-specific command should accept `--workspace`:

```powershell
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

This keeps future workspaces self-contained and prevents reports, generated tasks, and run evidence from being scattered across global folders.
