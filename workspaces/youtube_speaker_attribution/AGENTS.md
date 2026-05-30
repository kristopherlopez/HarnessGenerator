# AGENTS.md

## Workspace Purpose

This workspace is the first task family for the harness generator:

```text
workspaces/youtube_speaker_attribution/
```

The task is conservative real-person speaker attribution for YouTube podcast
media. The workspace accepts audio/video, provider transcripts, and reviewed
segments, then produces timestamped transcript segments with speaker attribution,
confidence, evidence, and review status.

This file is task-specific. Do not copy these assumptions into the root
`AGENTS.md` or generic harness code unless they become reusable abstractions.

## Read First

Use this order for local context:

1. `task.yaml` for workspace paths, active artifacts, and promotion policy.
2. `docs/seeded_cleanup_workflow.md` for the current seed-gold review loop.
3. `docs/task-family.md` for task-family intent.
4. `contracts/output_contract.yaml` and `contracts/gold_dataset_contract.yaml` only when changing schemas.
5. `reports/` and `codex_tasks/` when optimizing harness behavior from eval failures.

## Active Dataset Workflow

- Gold calibration cases live in `datasets/seed_gold/cases/`.
- The active review dataset is `datasets/seeded_review_global/cases/`.
- `datasets/seeded_review/` is the older per-part Deepgram pass and is retained for comparison/debugging only.
- `datasets/drafts/` contains rough machine-generated or intake artifacts.
- `task.yaml` is the source of truth for `active_artifacts`.
- Generated review cases are not gold until explicitly promoted.

For the current YouTube source, review should continue from the
`active_artifacts.active_review_case` path in `task.yaml`:

```text
datasets/seeded_review_global/cases/youtube_gG1Lq2pIgGM_part_004.json
```

## Human Review Rules

- Do not overwrite `seed_gold` labels unless the user explicitly asks.
- Do not overwrite segments marked by `evidence_types: ["human_review", ...]` unless the user explicitly corrects them.
- Preserve segment IDs as contiguous integers after splits.
- When splitting a segment, use provider word timings where possible.
- Mark human-corrected segments with `human_review` evidence and a note explaining the source segment/provider word range.
- Keep generated review material separate from promoted gold.

## Deepgram Rules

- Prefer the full-clip Deepgram response for chunked podcast review:
  `datasets/drafts/provider_outputs/deepgram_diarized_transcription/youtube_gG1Lq2pIgGM.json`
- The global seeded review profile is:
  `datasets/seed_gold/calibration/seed_gold_profile_global.json`
- Per-part Deepgram speaker IDs are not stable across separate five-minute API calls.
- Treat provider speaker IDs as evidence, not identity truth.
- Do not call Deepgram unless the user asks or the required cached provider output is missing and regeneration is necessary.
- Never print `DEEPGRAM_API_KEY` or any `.env` value.

## Commands

Run focused dataset checks:

```powershell
uv run pytest tests/test_seed_gold.py tests/test_draft_cases.py
```

Run the full test suite:

```powershell
uv run pytest
```

Run lint and type checks:

```powershell
uv run ruff check .
uv run mypy app evals
```

Run small-gold eval:

```powershell
uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

Compare strategies:

```powershell
uv run python -m evals.compare_strategies --workspace workspaces/youtube_speaker_attribution --dataset small_gold
```

Check regressions:

```powershell
uv run python -m evals.check_regression --workspace workspaces/youtube_speaker_attribution
```

Promote a reviewed global case into `seed_gold`:

```powershell
uv run python -m app.calibration.seed_gold promote-review `
  --workspace workspaces/youtube_speaker_attribution `
  --source-dataset seeded_review_global `
  youtube_gG1Lq2pIgGM_part_004.json
```

Regenerate the global seeded review set from the full Deepgram response:

```powershell
@'
from pathlib import Path
import json
from app.calibration.seed_gold import build_seed_profile_from_manifest, generate_seeded_review_cases

workspace = Path("workspaces/youtube_speaker_attribution")
profile_path = workspace / "datasets" / "seed_gold" / "calibration" / "seed_gold_profile_global.json"
provider_case_name = "youtube_gG1Lq2pIgGM.json"
build_seed_profile_from_manifest(
    workspace,
    output_path=profile_path,
    provider_case_name=provider_case_name,
)
seed_names = set(json.loads((workspace / "datasets" / "seed_gold" / "manifest.json").read_text())["cases"])
generate_seeded_review_cases(
    workspace,
    profile_path=profile_path,
    target_glob="youtube_gG1Lq2pIgGM_part_*.json",
    exclude_case_names=seed_names,
    output_dataset="seeded_review_global",
    provider_case_name=provider_case_name,
)
'@ | uv run python -
```

## Definition Of Done

For label or dataset edits:

- schema validation passes through the dataset loader
- segment IDs remain contiguous after edits
- focused dataset tests pass
- human-reviewed provenance is preserved

For resolver, strategy, threshold, or scoring changes:

- tests pass
- lint and type checks pass
- relevant evals run
- reports show before/after impact
- false-assignment risk does not increase without explicit acceptance

## Review Focus

When reviewing this workspace, prioritize:

- wrong real-person attribution
- speaker overlap and rapid handoff boundaries
- provider speaker drift across chunks
- generated review output being promoted without human review
- missing evidence provenance
- public exposure of biometric internals
