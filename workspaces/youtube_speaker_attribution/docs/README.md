# YouTube Speaker Attribution Workspace Docs

These docs describe the `workspaces/youtube_speaker_attribution` task workspace: its task family,
dataset workflows, resolver behavior, identity registry assumptions, and review process.

Project-level HarnessGenerator docs live in the repository-level [docs](../../../docs/README.md)
directory.

## Workspace Design

- [Task family](task-family.md)
- [Resolver strategies](resolver_strategies.md)
- [Failure modes](failure_modes.md)
- [Registry design](registry_design.md)
- [Gold dataset output](gold_dataset_output.md)

## Operator Workflows

- [Bootstrapping without gold labels](bootstrapping_without_gold.md)
- [Progressive dataset workflow](progressive_dataset_workflow.md)
- [Seeded cleanup workflow](seeded_cleanup_workflow.md)
