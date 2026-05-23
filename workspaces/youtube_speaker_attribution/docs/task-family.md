# Task Family: YouTube Podcast Speaker Attribution

## Goal

Given a YouTube podcast episode, generate an accurate timestamped transcript with each spoken segment attributed to the correct speaker.

The benchmark should measure whether a harness can do more than transcribe audio. It must decide who spoke when, map anonymous diarization labels to real speaker names, handle interruptions and overlapping speech, and produce a transcript that can be audited by a human.

The safety bias is conservative: prefer `unknown` or `needs_review` over assigning the wrong real person.

## Input

Each task instance represents one podcast episode or episode excerpt.

Minimum input:

- `episode_id`
- `source_type`: `youtube_url`, `local_audio`, `local_video`, or `caption_file`
- `source_uri`
- `known_speakers`: expected names when available
- `speaker_hints`: optional host/guest metadata, descriptions, show notes, or title
- `reference_available`: whether the instance has hidden labels for scoring

Preferred input for accurate benchmarking:

- Local audio or video file under user control.
- Human-labeled reference transcript.
- Optional short reference clips for known speakers.
- Episode metadata with host and guest names.

## Output

The harness must produce structured output:

```json
{
  "episode_id": "example-001",
  "speakers": [
    {"id": "speaker_0", "name": "Host Name", "confidence": 0.92},
    {"id": "speaker_1", "name": "Guest Name", "confidence": 0.88}
  ],
  "segments": [
    {
      "start": 12.34,
      "end": 18.91,
      "speaker_id": "speaker_0",
      "speaker_name": "Host Name",
      "text": "Welcome back to the show.",
      "confidence": 0.91
    }
  ],
  "needs_review": [
    {
      "start": 241.2,
      "end": 247.9,
      "reason": "overlapping_speech"
    }
  ]
}
```

The authoritative machine-readable output requirements come from the merged contract set:
`bootstrap/output_contract.yaml` plus
`workspaces/youtube_speaker_attribution/contracts/output_contract.yaml` when the workspace is
selected.

## Current Baseline And Ingestion State

The first runnable baseline is deliberately simple and safe:

1. Load labelled transcript fixtures.
2. Return diarized speaker labels with `unknown` real-person identity.
3. Score false-assignment rate, unknown rate, and identity accuracy.
4. Compare against conservative resolver strategies.
5. Generate one narrow Codex task from the highest-impact failure.

The workspace also has an opt-in draft-media workflow:

1. Ingest local audio/video or an authorized caption source.
2. Extract normalized audio.
3. Run transcription with diarization.
4. Normalize diarized segments into the project output schema.
5. Treat provider speakers as anonymous provisional labels until reviewed.
6. Promote only human-reviewed cases into gold or seed-gold datasets.
7. Resolve identities only when supported by non-LLM evidence.
8. Use an LLM only to explain conflicts, summarize review items, or generate Codex tasks.
9. Score reviewed cases against the reference transcript.

Implemented tooling currently includes YouTube intake seeding, media chunking with `ffmpeg`,
optional YouTube media preparation through `yt-dlp`, draft-case generation from media chunks,
Deepgram and OpenAI diarized transcription adapters, and seed-gold calibration for review-case
generation. Live provider calls are outside the normal test path and require explicit credentials.

The first generated candidates should optimize only the speaker-name resolution and transcript reconciliation steps. Raw generated code search should wait until ingestion, scoring, and trace capture are stable.

## Scoring

Primary safety metric:

- **False assignment rate:** rate at which a segment is assigned to the wrong real person.

Primary quality metric:

- **Speaker-attributed word accuracy:** percentage of reference words assigned to the correct speaker after timestamp/text alignment.

Secondary metrics:

- Word error rate.
- Diarization error rate.
- Speaker confusion matrix.
- Segment boundary F1 within a timestamp tolerance.
- Unknown-speaker rate.
- Human-review rate.
- Cost per audio hour.
- Latency per audio hour.

## Reference Data

A useful reference transcript should contain:

```json
{
  "episode_id": "example-001",
  "segments": [
    {
      "start": 12.2,
      "end": 18.8,
      "speaker_name": "Host Name",
      "text": "Welcome back to the show."
    }
  ]
}
```

Reference labels should stay hidden from candidate harnesses. The optimizer may see aggregate validation scores and failure summaries, but not held-out test labels.

## Ingestion Policy

YouTube ingestion must respect platform permissions and content rights. The system should support:

- User-provided local audio/video files.
- User-provided caption files.
- Authorized YouTube Data API caption access where the user has permission.
- Metadata-only YouTube URL handling when media/caption access is not available.
- User-authorized media preparation helpers for local review workflows.

The project should not depend on unofficial downloading as its default unattended path. Any
YouTube media download workflow is opt-in and should be used only when the user has the right to
process that media.

## Harness Search Space

Early search dimensions:

- Conservative assignment thresholds.
- Unknown and review thresholds.
- Minimum voice duration for identity evidence.
- False-assignment versus review-rate tradeoffs.
- Speaker-name resolution prompt.
- Whether to use episode metadata before or after diarization.
- How to merge short segments.
- How to handle interruptions and overlapping speech.
- Confidence thresholds for `needs_review`.
- Whether to run a second-pass LLM correction over low-confidence spans.

Later search dimensions:

- Transcription backend selection.
- Diarization backend selection.
- Speaker embedding/reference-clip matching.
- Ensemble strategies across diarization providers.
- Episode-level speaker memory.
- Code-level reconciliation strategies.

## Failure Modes

- Incorrectly mapping host and guest labels.
- Assigning intro ads, clips, or producer voices to main speakers.
- Speaker swaps after long monologues.
- Overlapping speech marked as a single speaker.
- Bad segment boundaries that shift attribution.
- Hallucinated words in transcript cleanup.
- Overusing LLM correction and changing what was actually said.
- Hidden reference leakage through traces or reports.
