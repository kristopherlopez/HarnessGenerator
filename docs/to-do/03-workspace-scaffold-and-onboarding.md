# To-Do: Workspace Scaffold And Onboarding Workflow

## Goal

Create a first-class process that guides people through creating a workspace before they run evals or candidate generation.

## Checklist

- [ ] Define the workspace creation flow:
  - choose task family name and workspace id
  - define task goal
  - define input schema
  - define output schema
  - define dataset format and splits
  - define scoring metrics
  - define safety constraints
  - define allowed tools and providers
  - define budgets
  - define baseline harness
  - define failure categories
  - define candidate search surfaces
- [ ] Add a scaffold command or script, for example:

```powershell
uv run python -m app.workspaces.scaffold --workspace workspaces/example_task
```

- [ ] Scaffold these files and folders:
  - `task.yaml`
  - `contracts/`
  - `datasets/`
  - `harnesses/`
  - `experiments/`
  - `runs/`
  - `codex_tasks/`
  - `reports/`
  - workspace `README.md`
- [ ] Add template contracts with placeholder values that fail readiness until completed.
- [ ] Add a tiny dataset fixture template and manifest template.
- [ ] Add a baseline harness template that returns a safe default output.
- [ ] Add an onboarding checklist document inside each new workspace.
- [ ] Add a Codex skill or project workflow document that asks the setup questions in order.
- [ ] Make the workflow stop before optimization if required answers are missing.

## Acceptance Criteria

- A user can create a new empty workspace without copying the YouTube workspace.
- The scaffolded workspace is intentionally not optimization-ready until required fields are filled.
- The scaffolded workspace can be checked by the readiness validator.

## Suggested Verification

```powershell
uv run pytest
uv run python -m app.workspaces.scaffold --workspace workspaces/example_task
uv run python -m app.workspaces.readiness --workspace workspaces/example_task
```
