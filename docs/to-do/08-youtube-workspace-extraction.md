# To-Do: YouTube Workspace Extraction

## Goal

Keep the first workspace fully supported while removing its assumptions from generic defaults and root-level engine code.

## Checklist

- [ ] Move or clearly scope YouTube-specific docs:
  - task family description
  - resolver strategies
  - speaker-attribution failure modes
  - registry design if it remains identity-specific
- [ ] Replace root `bootstrap/*.yaml` identity defaults with generic defaults or templates.
- [ ] Keep YouTube-specific contract overrides under `workspaces/youtube_speaker_attribution/contracts/`.
- [ ] Move identity-specific strategy registration behind a YouTube adapter.
- [ ] Move identity-specific dataset models behind a YouTube adapter.
- [ ] Move identity-specific metrics behind a YouTube adapter.
- [ ] Move YouTube-specific candidate proposal templates behind a YouTube template provider.
- [ ] Replace `DEFAULT_WORKSPACE = workspaces/youtube_speaker_attribution` with explicit workspace handling or a documented demo default.
- [ ] Review root `AGENTS.md` and decide whether speaker-attribution rules belong in:
  - workspace `AGENTS.md`
  - workspace README
  - task-specific docs
  - generic safety docs
- [ ] Preserve existing commands for the YouTube workspace.
- [ ] Add migration notes for any changed command paths or report locations.

## Acceptance Criteria

- A generic workspace does not inherit speaker-attribution fields by default.
- The YouTube workspace still passes readiness, eval, comparison, and regression checks.
- Docs make it obvious which YouTube assets are examples and which are required engine concepts.

## Suggested Verification

```powershell
uv run pytest
uv run python -m app.bootstrap.readiness --workspace workspaces/youtube_speaker_attribution
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
uv run python -m evals.compare_strategies --workspace workspaces/youtube_speaker_attribution --dataset small_gold
uv run python -m evals.check_regression --workspace workspaces/youtube_speaker_attribution
```
