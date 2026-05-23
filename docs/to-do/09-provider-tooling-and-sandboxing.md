# To-Do: Provider Tooling And Sandboxing

## Goal

Make model providers, external tools, and generated candidate code safe and configurable across workspaces.

## Checklist

- [ ] Define generic provider interfaces for:
  - LLM calls
  - embedding or retrieval tools where applicable
  - task-specific external tools
  - local deterministic tools
- [ ] Keep workspace tool policy explicit:
  - allowed tools
  - blocked tools
  - network access
  - filesystem reads
  - filesystem writes
  - paid API access
  - cache policy
- [ ] Require mocked providers in tests unless a task explicitly permits live external API checks.
- [ ] Add provider capability metadata:
  - cost model
  - latency estimate
  - cacheability
  - deterministic or stochastic behavior
  - required secrets
- [ ] Redact secrets from traces, reports, exceptions, and archived configs.
- [ ] Add sandbox policy for generated code:
  - import allowlist
  - file allowlist
  - network disabled by default
  - CPU, memory, and wall-clock limits
  - no shell access by default
- [ ] Add review gates for:
  - new imports
  - shell execution
  - network access
  - writes outside the run directory
  - high-cost candidate plans
- [ ] Include tool and provider usage in run reports.

## Acceptance Criteria

- Workspace contracts explicitly state whether networked or paid tools are allowed.
- Tests do not call live external APIs by default.
- Generated code cannot access hidden labels, secrets, or arbitrary filesystem paths.
- Tool usage and provider cost are visible in reports.

## Current Progress

- `app.media.prepare` provides local media chunking and opt-in YouTube media preparation through
  external `ffmpeg`/`yt-dlp` commands.
- `app.transcription.deepgram` and `app.transcription.openai_diarized` populate draft cases from
  diarized provider responses and cache raw provider output under `datasets/drafts/provider_outputs/`.
- Tests exercise provider-response normalization without live external API calls.
- Generic provider interfaces, cost metadata, trace redaction, and generated-code sandboxing remain
  open.

## Suggested Verification

```powershell
uv run pytest
uv run ruff check .
uv run mypy app evals
```
