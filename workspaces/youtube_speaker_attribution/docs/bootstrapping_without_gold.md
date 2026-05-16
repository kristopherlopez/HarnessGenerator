# Bootstrapping Without Gold Labels

You can start with a YouTube URL, but the first automatically produced dataset should be treated as **silver**, not gold.

Gold means reviewed truth. Silver means model-generated or mechanically converted labels that are useful for bootstrapping, debugging, and prioritizing review.

## First Sample Flow

1. Seed the source:

   ```powershell
   uv run python -m app.intake.youtube_seed "https://www.youtube.com/watch?v=gG1Lq2pIgGM" --workspace workspaces/youtube_speaker_attribution
   ```

2. Add or obtain transcript/audio through an allowed path:

   - user-provided media file in `datasets/drafts/media/`
   - user-provided caption file in `datasets/drafts/transcripts/`
   - authorized YouTube caption access
   - transcription/diarization provider output from a local media file

   To prepare a YouTube source into five-minute media chunks:

   ```powershell
   uv run python -m app.media.prepare --workspace workspaces/youtube_speaker_attribution --youtube-url "https://www.youtube.com/watch?v=gG1Lq2pIgGM" --segment-seconds 300
   ```

   This writes media under `datasets/drafts/media/<source_id>/` and creates `segments_manifest.json`.

3. Convert provider output into `datasets/silver/cases/<case_id>.json`.

4. Use the silver case to find likely speakers, rough timestamps, and ambiguous spans.

5. Promote only reviewed cases into `datasets/small_gold/cases/`.

## What Automation Can Do

Automation can produce:

- rough transcript text
- diarized speaker turns
- anonymous speaker IDs
- candidate speaker names
- confidence scores
- review flags

Automation cannot honestly produce gold labels without some trusted review source.

## Minimum Human Input

If you do not want to manually label everything, the lightest review loop is:

- confirm the clip range
- confirm the known speaker list
- review only low-confidence or identity-changing spans
- promote a small subset to `small_gold`
