# Harness Engineering Research Extracts

Last updated: 2026-06-02

This note records primary research articles discovered during the harness-loop
work. Exact word-for-word extracts are intentionally short; use the linked
papers for full text.

## Agentic Harness Engineering

Source: [Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses](https://arxiv.org/abs/2604.25850)

Exact extracts:

- "three matched observability pillars"
- "every edit into a falsifiable contract"

Relevance:

- Treat candidate harness changes as editable components with file-level state.
- Preserve run evidence in a form an optimizer can inspect.
- Record each candidate's predicted effect, then verify or falsify it after eval.

Project mapping:

- Component observability: generated candidate YAML under `experiments/generated_harnesses/`.
- Experience observability: eval reports, failure reports, run summaries, and harness history.
- Decision observability: generated candidate outcome reports with predictions, deltas, and next recommendations.

## AI Harness Engineering

Source: [AI Harness Engineering: A Runtime Substrate for Foundation-Model Software Agents](https://arxiv.org/abs/2605.13357)

Exact extracts:

- "model-harness-environment system"
- "auditable episode package"

Relevance:

- Agent performance should be evaluated as a model plus harness plus environment.
- Completion should be established through traces, failure attribution, and verification reports.
- Harness responsibilities should include task specification, context, tool access, memory, observability, failure attribution, verification, permissions, entropy auditing, and intervention recording.

Project mapping:

- The harness run result should remain the unit of audit.
- The API-shaped harness output should include enough metadata to reproduce and explain each run.
- History should preserve code state, metrics, decision rationale, and generated artifacts.

## Harness-Bench

Source: [Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows](https://arxiv.org/abs/2605.27922)

Exact extracts:

- "model-harness configuration level"
- "auditable agent execution stacks"

Relevance:

- Benchmarks should expose harness configuration effects, not only model choice.
- Each run should retain artifacts, traces, usage statistics, and validator outputs.
- Evaluation should preserve native execution behavior where possible.

Project mapping:

- Compare generated harness configs against the promoted baseline.
- Keep usage metadata and validation outcomes attached to each candidate report.
- Prefer deterministic validators and contract checks for promotion decisions.

## GEPA

Source: [GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457)

Exact extracts:

- "natural language reflection"
- "Pareto frontier"
- "few rollouts into a large quality gain"

Relevance:

- Reflection over trajectories can be more sample-efficient than scalar reward search alone.
- Keep diverse candidate lessons rather than only the current winner.
- Use failure evidence to propose mutations, then test them against held-out outcomes.

Project mapping:

- Candidate proposals should inspect failure reports, not only aggregate metrics.
- Outcome artifacts should preserve what each failed candidate taught.
- Future search should avoid repeating no-op or regressive mutation surfaces.

## DSPy

Source: [DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines](https://arxiv.org/abs/2310.03714)

Exact extracts:

- "text transformation graphs"
- "maximize a given metric"

Relevance:

- LLM programs can be expressed as structured modules rather than raw prompts.
- Optimization should target an explicit metric.
- The system should separate program structure from learned prompts, demos, or config.

Project mapping:

- Keep task adapters, runner contracts, and candidate configs explicit.
- Do not hide optimizer behavior inside free-form prompt strings.
- Let reports state which metric a candidate is supposed to improve.

## TextGrad

Source: [TextGrad: Automatic "Differentiation" via Text](https://arxiv.org/abs/2406.07496)

Exact extracts:

- "automatic ``differentiation'' via text"
- "textual feedback"

Relevance:

- Natural-language feedback can be propagated to improve individual components.
- Optimization variables can include prompts, code snippets, or other structured text.
- The objective function should be explicit enough that feedback can point to concrete edits.

Project mapping:

- Failure reports should identify the component likely responsible for the miss.
- Candidate outcome reports should convert failed predictions into next-edit guidance.
- Structured configs are a better first search surface than unconstrained code edits.

## Automatic Prompt Optimization

Source: [Automatic Prompt Optimization with "Gradient Descent" and Beam Search](https://arxiv.org/abs/2305.03495)

Exact extracts:

- "natural language \"gradients\""
- "beam search"

Relevance:

- Prompt changes can be generated from minibatch feedback rather than manual trial and error.
- Search efficiency improves when candidate edits are ranked and selected systematically.
- Training data and evaluation feedback are required for meaningful prompt optimization.

Project mapping:

- Use gold cases and failure reports to produce candidate mutations.
- Keep candidate generation bounded by a staged search space.
- Compare candidates with deterministic metrics before promotion.

## Promptbreeder

Source: [Promptbreeder: Self-Referential Self-Improvement Via Prompt Evolution](https://arxiv.org/abs/2309.16797)

Exact extracts:

- "self-referential self-improvement mechanism"
- "evaluates them for fitness"

Relevance:

- An outer loop can evolve not only task prompts, but also mutation prompts.
- Fitness evaluation is central; generated changes are not useful until scored.
- The mutation process itself can become an optimization target.

Project mapping:

- `propose_harness_loop` is the mutation step.
- `test_generated_harness_loop` is the fitness step.
- Candidate proposal templates can become future optimizer components once the reporting loop is stable.

## Design Takeaways For This Repository

- Every candidate should declare a hypothesis before it runs.
- Every eval should produce actual metric deltas against a known baseline.
- Every failed candidate should produce a next-step recommendation, not just a score.
- Generated artifacts should remain separate from promoted harnesses until checks pass.
- The loop should optimize harness components, not treat the LLM as the only source of improvement.
- The first safe search surface is config and workflow metadata; unrestricted code mutation should wait for stronger sandboxing and rollback.
