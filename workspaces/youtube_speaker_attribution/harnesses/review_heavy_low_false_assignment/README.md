# review_heavy_low_false_assignment

This harness is the current conservative candidate. It resolves strong multi-evidence matches, plus voice-only matches when confidence, duration, candidate margin, and provenance all clear the configured safety thresholds. It leaves weak or ambiguous cases as `unknown` or `needs_review`.

Long voice-only conflicts with close top candidates are routed to review with conflict provenance. Short or lower-confidence conflicts stay `unknown` to preserve the review budget.

High-overlap voice-only matches are not auto-assigned. They require corroborating `active_speaker` or `face` evidence before the harness resolves a real person.

It remains intentionally recall-limited until further candidate changes prove they can improve known-person recall without increasing false assignments.
