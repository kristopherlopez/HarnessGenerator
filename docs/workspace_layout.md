# Workspace Layout

HarnessGenerator uses a workspace-first layout. Reusable meta-system code stays at the repo root; task-specific artifacts live under `workspaces/<workspace_id>/`.

## Root-Level Engine

```text
app/        reusable contract loading, optimizer, and identity strategy code
bootstrap/  global default contracts
evals/      reusable eval runner modules
docs/       project-level documentation
tests/      engine and workspace behavior tests
```

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

## Command Pattern

Every task-specific command should accept `--workspace`:

```powershell
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

This keeps future workspaces self-contained and prevents reports, generated tasks, and run evidence from being scattered across global folders.
