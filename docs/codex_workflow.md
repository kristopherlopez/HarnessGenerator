# Codex Workflow

Codex must work through small, testable tasks.

The recursive loop is:

1. Run evals.
2. Mine failures.
3. Generate bounded harness candidate changes.
4. Select one candidate and generate a Codex task.
5. Codex implements only that task.
6. Tests and evals run.
7. Regression guards check safety.
8. PR is reviewed.
9. A human decides whether to merge.

Codex should not perform broad rewrites unless the task explicitly asks for one.

Generated tasks must include:

- observed failure
- affected cases
- suspected cause
- required change
- files likely to change
- files not to change
- acceptance criteria
- required tests
- eval command
- safety checks

Candidate proposals must include:

- failure type
- affected cases
- harness change surface
- expected metric effect
- risk notes
- files likely to change
- files not to change
- required commands

The recursion is in the failure-to-task-to-eval loop, not in unsupervised production-code mutation.
