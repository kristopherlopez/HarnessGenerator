# Gold Dataset Output

The system input can start as a YouTube link, but the gold dataset output is a reviewed truth file. It is the evaluator's source of truth and must not be visible to candidate harnesses during scoring.

## Gold Case Shape

Each reviewed case contains:

- source metadata: YouTube URL, source ID, title, and notes
- media metadata: local media path or clip path
- condition metadata: speaker count, overlap, face visibility, audio quality
- speaker list: known and unknown speakers expected in the clip
- segment labels: timestamped transcript spans with true speaker identity
- annotation status: draft, reviewed, or promoted

Use `datasets/small_gold/gold_case_template.json` as the template.

## Minimum Segment Fields

Each segment must include:

- `segment_id`
- `start`
- `end`
- `text`
- `true_person_id`
- `true_display_name`
- `speaker_type`

For unknown speakers:

```json
{
  "true_person_id": "unknown",
  "true_display_name": "Unknown Speaker",
  "speaker_type": "unknown"
}
```

## Promotion Rule

Draft cases live in `datasets/drafts/cases/`. A case should move into `datasets/small_gold/cases/` only when:

- segment timestamps are checked
- transcript text is reviewed enough for scoring
- speaker labels are reviewed
- unknown speakers are explicitly marked
- the case filename is added to `datasets/small_gold/manifest.json`

## Separation From Predictions

Gold cases use `true_person_id` and `true_display_name`.

Harness predictions use `person_id`, `display_name`, `confidence`, `resolution_status`, `evidence_summary`, and `review`.

The evaluator compares predictions against gold labels.

