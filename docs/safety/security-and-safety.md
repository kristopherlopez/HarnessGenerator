# Security and Safety

HarnessGenerator will eventually execute generated candidate code and model-produced tool calls. Security is therefore a core design requirement.

## Secrets

- Store provider keys in `.env` or the host secret manager.
- Never write API keys to traces, prompts, reports, or archives.
- Redact credentials from environment snapshots and exception messages.
- Do not expose secrets to generated candidate code unless explicitly required.

## Sandboxing

Generated code should run with:

- Temporary working directories.
- Network disabled by default.
- File read/write allowlists.
- CPU, memory, wall-clock, and process limits.
- Tool allowlists.
- No shell access unless the task specifically requires it.

## Data Leakage

The runner must prevent candidates from accessing:

- Test labels.
- Private benchmark examples.
- Full aggregate test feedback during optimization.
- Other candidates' hidden outputs unless the experiment allows archive access.

## Tool Safety

- Prefer mocked tools for evaluation.
- Log tool name, arguments, result, latency, and errors.
- Validate arguments before executing external actions.
- Require explicit opt-in for networked tools, file mutation, or paid APIs.

Current provider/media commands are operator tools, not candidate-executed tools. `yt-dlp`,
`ffmpeg`, Deepgram, and OpenAI transcription commands should be run only when explicitly requested
for draft data preparation. Tests must continue to use local fixtures or mocked provider responses,
not live external APIs.

## Human Review Gates

Before enabling open-ended code search, require review for:

- New imports.
- Shell execution.
- Network access.
- File writes outside the run directory.
- Long-running or high-cost candidate plans.

## Audit Trail

Each run should record:

- Task spec version.
- Dataset fingerprint.
- Candidate source hash.
- Model and provider versions.
- Budget limits.
- Tool permissions.
- Scores and failures.
- Any human intervention.
