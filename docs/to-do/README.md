# HarnessGenerator To-Do Lists

This folder tracks the work needed to make HarnessGenerator usable across multiple task workspaces and to add a first-class workflow for creating new workspaces safely.

The lists are split so each part can be completed independently. Some lists will become easier after earlier ones land, but each has its own acceptance criteria and should avoid broad rewrites.

## Index

| File | Scope | Can Be Completed Independently |
| --- | --- | --- |
| [01-project-boundaries-and-docs.md](01-project-boundaries-and-docs.md) | Clarify generic engine vs first workspace in docs | Yes |
| [02-generic-contract-system.md](02-generic-contract-system.md) | Make contract validation task-agnostic | Yes, with compatibility tests |
| [03-workspace-scaffold-and-onboarding.md](03-workspace-scaffold-and-onboarding.md) | Add the first-class workspace creation workflow | Yes |
| [04-readiness-validation-gate.md](04-readiness-validation-gate.md) | Block optimization until a workspace is ready | Yes |
| [05-adapter-interfaces.md](05-adapter-interfaces.md) | Define generic task, dataset, scorer, and strategy interfaces | Yes |
| [06-eval-runner-archive-traces.md](06-eval-runner-archive-traces.md) | Generalize eval execution, reports, archives, and traces | Yes |
| [07-candidate-generation-and-task-loop.md](07-candidate-generation-and-task-loop.md) | Generalize failure-to-candidate-to-Codex-task loop | Yes |
| [08-youtube-workspace-extraction.md](08-youtube-workspace-extraction.md) | Move YouTube-specific assumptions out of generic defaults | Yes |
| [09-provider-tooling-and-sandboxing.md](09-provider-tooling-and-sandboxing.md) | Generalize provider/tool policy and generated-code safety | Yes |
| [10-ci-and-regression-gates.md](10-ci-and-regression-gates.md) | Add test and CI gates for generic and workspace-specific behavior | Yes |
| [11-harness-hypothesis-and-api.md](11-harness-hypothesis-and-api.md) | Define generated harness hypotheses and the stable Harness API | Yes |

## Shared Definition Of Done

- The change has focused tests for the behavior it adds or changes.
- The YouTube speaker-attribution workspace still passes its existing eval and regression commands unless the task explicitly changes those contracts.
- New generic behavior is exercised by a small non-YouTube fixture or fake workspace.
- Documentation says which parts are generic and which parts are workspace-specific.
- The optimizer cannot run against an incomplete or unsafe workspace.
