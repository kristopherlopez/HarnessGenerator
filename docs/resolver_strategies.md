# Resolver Strategies

Resolver strategies convert transcript, diarization, face, voice, metadata, and review evidence into final speaker identities.

## Initial Strategies

- `baseline_unknown`: never assigns a real person automatically.
- `voice_only_knn`: assigns from voice similarity when confidence and duration are high enough.
- `face_only_knn`: assigns from face similarity when quality and active-speaker evidence are strong.
- `voice_face_weighted_sum`: combines voice and face candidates conservatively.
- `review_heavy_low_false_assignment`: resolves strong multimodal matches, resolves voice-only
  matches only when confidence, duration, candidate margin, and provenance are strong, and pushes
  ambiguous cases to review.

## Strategy Requirements

Every strategy must:

- produce contract-compliant output
- provide evidence summaries
- support unknown speakers
- avoid overwriting human labels
- expose thresholds through config
- include tests and eval output

## Conservative Voice-Only Path

The `review_heavy_low_false_assignment` strategy allows a voice-only assignment only when all of
these configured thresholds are met:

- `voice_only_assignment_threshold`: minimum top voice candidate confidence.
- `voice_only_margin_threshold`: minimum margin over the runner-up candidate.
- `min_voice_only_duration_seconds`: minimum voice duration for a voice-only assignment.

These thresholds are stricter than generic review handling so short utterances, weak voice matches,
and similar-voice conflicts remain `unknown` or `needs_review`.

When two long voice-only candidates are close enough to fail the voice-only margin threshold, the
strategy marks the segment `needs_review` with `ambiguous_voice_candidate_margin` instead of
discarding the evidence as generic weak evidence. Short or low-confidence conflicts still remain
`unknown` to preserve the review budget.

## Review Budget

The conservative strategy applies review routing in two passes:

- segment-level checks identify eligible `needs_review` segments
- case-level budgeting keeps the highest-confidence review candidates up to `max_review_rate`

When the budget is exceeded, lower-priority review candidates are emitted as `unknown` with
`review_budget_exceeded` while preserving non-sensitive evidence provenance. `minimum_review_slots`
allows short cases to retain one review candidate when any segment is eligible.

## Overlap Handling

The `require_corroborating_signal_on_high_overlap` policy prevents high-overlap voice-only evidence
from resolving a real-person identity. High-overlap segments can still resolve when the top candidate
has corroborating evidence such as `active_speaker` or `face` and clears the normal assignment
thresholds. Otherwise, high-confidence voice-only overlap evidence is routed to review or left
`unknown` under the review budget.

## Optimization Bias

The first benchmark optimizes for low false-assignment rate before recall. A transcript with more `needs_review` segments is preferable to a transcript that confidently assigns a real person incorrectly.
