# Seeded Cleanup Workflow

Reviewed chunks become `seed_gold` and calibrate the cleanup pass for the remaining
chunks. Generated output is review material, not gold.

## Generated Assets

- `datasets/seed_gold/cases/youtube_gG1Lq2pIgGM_part_000.json`
  - Human-cleaned seed case copied from `datasets/drafts/cases/`.
- `datasets/seed_gold/cases/youtube_gG1Lq2pIgGM_part_001.json`
  - Human-cleaned seed case promoted from `datasets/seeded_review/cases/`.
- `datasets/seed_gold/cases/youtube_gG1Lq2pIgGM_part_002.json`
  - Human-cleaned seed case promoted from `datasets/seeded_review/cases/`.
- `datasets/seed_gold/cases/youtube_gG1Lq2pIgGM_part_003.json`
  - Human-cleaned seed case promoted from `datasets/seeded_review_global/cases/`.
- `datasets/seed_gold/calibration/seed_gold_profile.json`
  - Combined known speaker roster, Deepgram speaker mapping, and reference spans.
- `datasets/seeded_review_global/cases/youtube_gG1Lq2pIgGM_part_004.json` through
  `youtube_gG1Lq2pIgGM_part_010.json`
  - Active machine-generated review drafts for the remaining chunks.

## Current Calibration

From the cleaned seeds and global Deepgram pass, the active provider-speaker mapping is:

- Deepgram speaker `1` -> Denan Kemp, high confidence.
- Deepgram speaker `2` -> Sandor Earl, high confidence.
- Deepgram speaker `3` -> Matthew Buxton, based on promoted seed examples.
- Deepgram speaker `0` -> ambiguous; treat as review-required rather than a stable identity assignment.

## Review Findings

After promoting `part_002`, the observed confusion pattern is concentrated in
speaker overlap and very short gaps where one speaker starts immediately after
another. Future harness iterations should score these as separate boundary
stress cases rather than broad identity failures.

Early review of `part_003` also shows that Deepgram speaker IDs can shift across
separately processed five-minute chunks. The `seed_provider_speaker_map` should
therefore be treated as candidate evidence, not as a stable identity assignment,
until a chunk has local human anchors. This is most visible when one speaker ID
that mapped cleanly in `part_002` is assigned to a different person in `part_003`.

## Global Deepgram Pass

The project now also has a single full-clip Deepgram response:

- `datasets/drafts/provider_outputs/deepgram_diarized_transcription/youtube_gG1Lq2pIgGM.json`

This response was generated from the full local `source.mp4`, then sliced back
into five-minute review cases in `datasets/seeded_review_global/`. Because the
diarization is produced in one pass, speaker IDs are more stable across chunk
boundaries than the original per-part Deepgram outputs.

The global calibration profile is:

- `datasets/seed_gold/calibration/seed_gold_profile_global.json`

To regenerate the global review set:

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

## Regenerate

```powershell
uv run python -m app.calibration.seed_gold bootstrap `
  --workspace workspaces/youtube_speaker_attribution `
  --seed-case youtube_gG1Lq2pIgGM_part_000.json `
  --target-glob "youtube_gG1Lq2pIgGM_part_*.json"
```

To promote a reviewed generated case:

```powershell
uv run python -m app.calibration.seed_gold promote-review `
  --workspace workspaces/youtube_speaker_attribution `
  youtube_gG1Lq2pIgGM_part_001.json
```

To promote a reviewed global generated case:

```powershell
uv run python -m app.calibration.seed_gold promote-review `
  --workspace workspaces/youtube_speaker_attribution `
  --source-dataset seeded_review_global `
  youtube_gG1Lq2pIgGM_part_004.json
```

To rebuild from all current seed cases:

```powershell
uv run python -m app.calibration.seed_gold profile `
  --workspace workspaces/youtube_speaker_attribution

uv run python -m app.calibration.seed_gold generate-review `
  --workspace workspaces/youtube_speaker_attribution `
  --target-glob "youtube_gG1Lq2pIgGM_part_*.json"
```

## Review Loop

1. Review the next generated case from `active_artifacts.active_review_case` in `task.yaml`.
2. Correct speaker attribution and word-boundary splits.
3. Promote the cleaned file into `seed_gold` when it is reliable.
4. Regenerate the profile and review drafts.

Each reviewed chunk strengthens the mapping and creates better examples for later
parts.

The older `datasets/seeded_review/` directory is retained as the original
per-part Deepgram pass for comparison. Continue new review work from
`datasets/seeded_review_global/` unless specifically investigating per-part
diarization drift.
