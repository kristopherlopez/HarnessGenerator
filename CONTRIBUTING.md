# Contributing

## Development Principles

- Keep experiments reproducible from checked-in specs and archived run configs.
- Separate task data, candidate harness code, traces, and reports.
- Prefer deterministic evaluators before adding LLM-as-judge scoring.
- Add safety checks before expanding the candidate search space.
- Do not commit provider keys, `.env` files, private benchmark data, or paid API traces.

## Documentation Changes

When changing architecture or evaluation behavior, update the relevant file in `docs/` in the same change.

## Future Code Standards

The runtime implementation should include:

- Typed task and result objects.
- Structured logs.
- Unit tests for scoring and split handling.
- Integration tests for at least one tiny local dataset.
- Clear boundaries between candidate code and optimizer code.

