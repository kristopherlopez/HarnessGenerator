# Progressive Dataset Workflow

The workspace supports starting with YouTube links and building `small_gold` progressively.

## Stages

1. **Queued source**

   Add a row to `intake/youtube_links.jsonl` with the YouTube URL, expected speakers, useful timestamp ranges, and notes.

2. **Draft case**

   Copy `datasets/small_gold/gold_case_template.json` or `datasets/drafts/case_template.json` into `datasets/drafts/cases/<case_id>.json`. Fill in metadata first. Segments can be incomplete while you annotate.

3. **Local media**

   Add downloaded or clipped media under `datasets/drafts/media/` if you have rights to use it. The project should not depend on unofficial YouTube downloading as the default ingestion path.

4. **Reviewed labels**

   Once transcript text, timestamps, and `true_person_id` labels are reviewed, move the case JSON into `datasets/small_gold/cases/`, put media under `datasets/small_gold/media/`, and add the case filename to `datasets/small_gold/manifest.json`.

5. **Eval-ready**

   Run:

   ```powershell
   uv run python -m evals.run_eval --workspace workspaces/youtube_speaker_attribution --dataset small_gold
   ```

## Rule

`small_gold` is for reviewed ground truth. Use `intake/` and `datasets/drafts/` for links, rough notes, partial transcripts, and unreviewed annotations.
