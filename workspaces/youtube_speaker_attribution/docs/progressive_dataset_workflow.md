# Progressive Dataset Workflow

The workspace supports starting with YouTube links and building `small_gold` progressively.

## Stages

1. **Queued source**

   Add a row to `intake/youtube_links.jsonl` with the YouTube URL, expected speakers, useful timestamp ranges, and notes.

2. **Draft case**

   Seed a draft case from a YouTube URL with `app.intake.youtube_seed`, or copy
   `datasets/small_gold/gold_case_template.json` / `datasets/drafts/case_template.json` into
   `datasets/drafts/cases/<case_id>.json`. Fill in metadata first. Segments can be incomplete while
   you annotate.

3. **Local media and chunks**

   Add downloaded or clipped media under `datasets/drafts/media/` if you have rights to use it.
   `app.media.prepare` can segment a local file or, when explicitly requested, prepare a YouTube
   URL through `yt-dlp` and `ffmpeg`. `app.media.draft_cases` turns the segment manifest into
   chunk-level draft cases. The project should not depend on unofficial YouTube downloading as the
   default unattended ingestion path.

4. **Provider-populated review material**

   Deepgram and OpenAI diarized adapters can populate `datasets/drafts/cases/` from cached or live
   provider responses. These machine labels are review material only; provider speaker IDs are not
   real-person identity truth.

5. **Reviewed labels**

   Once transcript text, timestamps, and `true_person_id` labels are reviewed, move the case JSON into `datasets/small_gold/cases/`, put media under `datasets/small_gold/media/`, and add the case filename to `datasets/small_gold/manifest.json`.

6. **Eval-ready**

   Run:

   ```powershell
   uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
   ```

## Rule

`small_gold` is for reviewed ground truth. Use `intake/` and `datasets/drafts/` for links, rough notes, partial transcripts, and unreviewed annotations.
