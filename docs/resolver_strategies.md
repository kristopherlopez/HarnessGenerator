# Resolver Strategies

Resolver strategies convert transcript, diarization, face, voice, metadata, and review evidence into final speaker identities.

## Initial Strategies

- `baseline_unknown`: never assigns a real person automatically.
- `voice_only_knn`: assigns from voice similarity when confidence and duration are high enough.
- `face_only_knn`: assigns from face similarity when quality and active-speaker evidence are strong.
- `voice_face_weighted_sum`: combines voice and face candidates conservatively.
- `review_heavy_low_false_assignment`: pushes ambiguous cases to review.

## Strategy Requirements

Every strategy must:

- produce contract-compliant output
- provide evidence summaries
- support unknown speakers
- avoid overwriting human labels
- expose thresholds through config
- include tests and eval output

## Optimization Bias

The first benchmark optimizes for low false-assignment rate before recall. A transcript with more `needs_review` segments is preferable to a transcript that confidently assigns a real person incorrectly.

