# Workspace Layout

HarnessGenerator uses a workspace-first layout. Reusable meta-system code stays at the repo root; task-specific artifacts live under `workspaces/<workspace_id>/`.

## Root-Level Engine

```text
app/adapters/        task adapter protocols plus YouTube and simple_qa adapters
app/bootstrap/       contract readiness CLI
app/calibration/     seed-gold and review-case generation helpers
app/harness_optimizer/ candidate proposal and generated-task helpers
app/identity/        current YouTube speaker-attribution models and strategies
app/intake/          YouTube intake seeding
app/media/           media preparation and draft-case generation
app/transcription/   Deepgram and OpenAI diarized transcription adapters
bootstrap/           global default contracts and first-workspace-seeded defaults to extract
evals/               eval entrypoints plus current first-workspace scorer glue
docs/                project-level HarnessGenerator documentation
tests/               engine and workspace behavior tests
```

Root code should move toward generic contracts, adapters, runners, optimizers, reports, and safety
gates. Current identity-resolution modules are wrapped by a YouTube task adapter for eval and
strategy-comparison flows, but they are still rooted in the first workspace's schema and metrics.

## Task Workspace

```text
workspaces/youtube_speaker_attribution/
├── task.yaml
├── intake/
├── contracts/
├── datasets/
├── docs/
├── harnesses/
├── experiments/
├── runs/
├── codex_tasks/
└── reports/
```

`task.yaml` is the workspace manifest. It names the task family and declares where its contracts, datasets, harnesses, runs, experiments, generated tasks, and reports live.

`intake/` stores raw source links and notes before they become dataset cases.

`contracts/` contains task-specific overrides for global defaults. The loader reads `bootstrap/` first, then applies matching workspace contract files.

`datasets/` contains prepared task cases: labelled fixtures, draft/review cases, seed-gold or other
calibration cases, and future train, validation, test, regression, and adversarial sets. Use
`datasets/drafts/` for partial annotations and provider-populated review material. Use gold splits
only for reviewed ground truth. Generated or calibrated review datasets are not gold until a
workspace's review policy promotes them.

`docs/` contains workspace-specific docs, including task-family design, resolver strategies,
failure modes, registry assumptions, bootstrapping without gold labels, gold output shape,
progressive dataset workflow, and seeded cleanup workflow.

`harnesses/` contains promoted, reviewable harnesses. Failed or temporary candidates should stay in `runs/` or `experiments/` unless promoted.

`experiments/` is reserved for ablation plans and comparison reports that are not the current
latest report.

`runs/` is for immutable run evidence: harness snapshots, metrics, failures, traces, and reports.

`codex_tasks/` contains generated task templates and candidate implementation tasks.

`reports/` contains latest eval, failure, strategy-comparison, readiness, and candidate-proposal reports.

## Workspace Requirements

A workspace needs more than an evaluation set before HarnessGenerator should optimize it. It must provide:

- `task.yaml` with workspace id, task family, default dataset, default baseline or strategy, and paths
- task-specific contracts for input, output, metrics, safety, datasets, tools, strategy space, harness search space, and generated-task policy
- data-provisioning workflow for raw inputs, permissions, source-to-case transformation, cache policy, and review/gold promotion
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
uv run python -m app.workspaces.readiness --workspace workspaces/youtube_speaker_attribution
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

This keeps future workspaces self-contained and prevents reports, generated tasks, and run evidence from being scattered across global folders.

Current workspace report defaults write into `workspaces/<workspace_id>/reports/`. Generated Codex
tasks write into `workspaces/<workspace_id>/codex_tasks/generated/`.
