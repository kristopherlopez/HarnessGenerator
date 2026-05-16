Give Codex a repo with contracts, examples, tests, and task templates. Do not give it only a prompt.

The recursive improvement setup is:

contracts + datasets + evals + traces
→ harness identifies failure
→ harness writes Codex task
→ Codex implements small change
→ CI runs tests/evals
→ Codex reviews PR
→ human merges
→ new traces and reviews become more eval data

Codex should not “self-improve” by directly changing production code unsupervised. It should work through PR-sized tasks with acceptance criteria.

What to provide to Codex

Use all of these:

AGENTS.md
README.md
docs/_.md
bootstrap/_.yaml
evals/datasets/_
evals/reports/_
prompts/codex_tasks/_
tests/_

Each has a different job.

Artefact Purpose
AGENTS.md Standing instructions for Codex
Markdown docs Human-readable architecture, rules, schemas, workflow
YAML contracts Machine-readable config for the harness
Seed datasets Ground truth for discovering better methods
Eval reports Evidence of what is failing
Codex task templates Format for generated improvement tasks
Tests Hard guardrails
CI workflow Blocks unsafe regressions

OpenAI’s Codex docs say Codex reads AGENTS.md before doing work, and that this file is the right place for repo-specific instructions, commands, conventions, and expectations. Codex’s GitHub review can also follow repository guidance and be triggered with @codex review or automatic reviews.

1. AGENTS.md: the standing law

This is what you give Codex at the repo root.

# AGENTS.md

## Project purpose

This repository builds a multimodal identity-resolution harness for speaker-attributed transcription.

The system accepts audio/video and returns transcript segments with:

- diarisation speaker labels
- resolved real-person identity where evidence is strong
- unknown speaker labels where identity is not known
- confidence scores
- evidence summaries
- human-review flags

The domain includes approximately 200–300 known speakers.

## Non-negotiable rules

- Prefer unknown or needs_review over wrong real-person attribution.
- Do not make identity assignments without evidence provenance.
- Do not expose raw face embeddings, voice embeddings, face crops, or raw frames through public API responses.
- Do not overwrite human-reviewed labels.
- Do not allow LLM calls to be the only source of identity truth.
- Do not change public API schemas unless the task explicitly asks for it.
- Do not modify safety contracts unless the task explicitly asks for it.
- Do not use live external APIs in tests.
- Do not add resolver logic without tests and eval output.
- Do not hardcode thresholds without adding them to config and docs.

## Commands

Install:
`uv sync`

Run tests:
`uv run pytest`

Run lint:
`uv run ruff check .`

Run type checks:
`uv run mypy app evals`

Run evals:
`uv run python -m evals.run_eval --dataset evals/datasets/small_gold`

Compare strategies:
`uv run python -m evals.compare_strategies --dataset evals/datasets/small_gold`

Check regressions:
`uv run python -m evals.check_regression --report evals/reports/latest.json`

Generate next Codex task:
`uv run python -m app.harness_optimizer.next_task --eval-report evals/reports/latest.json --failure-report evals/failures/latest_failures.json --output prompts/codex_tasks/generated/next_task.md`

## Definition of done

A change is done only when:

- tests pass
- lint passes
- relevant evals run
- identity logic changes include regression tests
- eval report shows before/after metric impact
- public API contract is preserved unless explicitly changed
- biometric safety rules are preserved
- docs are updated when contracts or resolver behaviour changes

## Review focus

When reviewing PRs, flag:

- false-assignment risk
- false-merge risk
- identity decisions without provenance
- missing open-set unknown handling
- public exposure of biometric internals
- missing regression tests
- metric gaming, especially improving recall while increasing false assignments

Keep this file concise. Put detail in docs and YAMLs. OpenAI’s best-practice guidance recommends reusable instructions and planning for difficult tasks, rather than repeating everything in every prompt.

2. Markdown docs: explain the system

Create these:

docs/
architecture.md
data_contracts.md
registry_design.md
resolver_strategies.md
eval_methodology.md
failure_modes.md
codex_workflow.md
privacy_security.md

Markdown is for things Codex and humans need to understand.

Example docs/codex_workflow.md:

# Codex Workflow

Codex must work through small, testable tasks.

The recursive loop is:

1. Run evals.
2. Mine failures.
3. Generate a Codex task.
4. Codex implements only that task.
5. Tests and evals run.
6. Regression guard checks safety.
7. PR is reviewed.
8. Human decides whether to merge.

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

3. YAML contracts: make discovery machine-readable

Markdown tells Codex what to understand. YAML tells the harness what to execute.

Create:

bootstrap/
domain_contract.yaml
input_contract.yaml
output_contract.yaml
tool_registry.yaml
strategy_space.yaml
metric_contract.yaml
safety_contract.yaml
dataset_manifest.yaml
review_policy.yaml
codex_task_policy.yaml
bootstrap/domain_contract.yaml
domain: multimodal_identity_resolution_for_speaker_attributed_transcription

goal:
produce_attributed_transcript_from_audio_or_video: true

population:
known_speakers_estimate_min: 200
known_speakers_estimate_max: 300
supports_unknown_speakers: true
supports_new_person_discovery: true

identity_policy:
prefer_unknown_over_wrong_identity: true
require_evidence_provenance: true
human_review_overrides_machine: true

primary_risk: false_assignment_to_real_person

secondary_risks:

- false_merge
- false_split
- registry_poisoning
- biometric_data_leakage
  bootstrap/output_contract.yaml
  transcript_segment:
  required_fields: - segment_id - start - end - text - speaker_id - person_id - display_name - confidence - resolution_status - evidence_summary - review

resolution_status:
allowed_values: - resolved - unknown - needs_review

speaker:
required_fields: - speaker_id - person_id - display_name - confidence - total_speaking_time_seconds - segments_count - status
bootstrap/tool_registry.yaml
tools:
transcription:
interface: TranscriptionProvider
implementations: - name: deepgram
enabled: true
cacheable: true
returns: - words - word_timings - utterances - confidence

diarisation:
interface: DiarisationProvider
implementations: - name: pyannote
enabled: true
cacheable: true
returns: - speaker_segments - speaker_labels

face_embedding:
interface: FaceEmbeddingProvider
implementations: - name: insightface
enabled: true
cacheable: true
returns: - face_embeddings - quality_score - model_version

voice_embedding:
interface: VoiceEmbeddingProvider
implementations: - name: default_voice_embedding_model
enabled: true
cacheable: true
returns: - voice_embeddings - quality_score - duration_seconds

llm:
interface: LlmReasoner
allowed_uses: - explain_conflict - summarise_review_item - classify_failure_mode - generate_codex_task
prohibited_uses: - final_identity_assignment_without_evidence - overwrite_human_review - infer_identity_from_transcript_alone
bootstrap/strategy_space.yaml
candidate_generation:

- voice_knn
- face_knn
- voice_centroid_match
- face_centroid_match
- local_voice_clustering
- local_face_clustering
- classifier_top_k
- hybrid_top_k

resolution_strategies:

- baseline_unknown
- voice_only_knn
- face_only_knn
- voice_face_weighted_sum
- cluster_then_match
- match_then_cluster
- active_speaker_first
- graph_fusion_conservative
- graph_fusion_aggressive
- classifier_rerank
- review_heavy_low_false_assignment

threshold_search:
enabled: true
parameters:
voice_candidate_min: [0.50, 0.60, 0.70, 0.80]
face_candidate_min: [0.40, 0.50, 0.60, 0.70]
assignment_threshold: [0.75, 0.80, 0.85, 0.90, 0.95]
review_threshold: [0.50, 0.60, 0.70]
margin_threshold: [0.03, 0.05, 0.08, 0.10, 0.15]
min_voice_duration_seconds: [1.0, 2.0, 2.5, 3.0, 5.0]

selection_policy:
optimise_for: lowest_false_assignment_rate
constraints:
max_false_assignment_rate: 0.02
max_review_rate: 0.25
bootstrap/metric_contract.yaml
primary_metric:
name: false_assignment_rate
lower_is_better: true

secondary_metrics:

- name: identity_accuracy
  lower_is_better: false
- name: known_person_precision
  lower_is_better: false
- name: known_person_recall
  lower_is_better: false
- name: unknown_detection_recall
  lower_is_better: false
- name: false_merge_rate
  lower_is_better: true
- name: false_split_rate
  lower_is_better: true
- name: needs_review_rate
  lower_is_better: true
- name: latency_seconds_per_media_hour
  lower_is_better: true

selection_rules:
winner_must: - preserve_output_contract - pass_regression_cases - not_increase_false_assignment_rate_above_limit - not_increase_false_merge_rate_above_limit
bootstrap/codex_task_policy.yaml
generated_task_must_include:

- title
- observed_failure
- affected_cases
- suspected_cause
- required_change
- files_likely_to_change
- files_not_to_change
- acceptance_criteria
- required_tests
- required_eval_command
- safety_checks

generated_task_must_not:

- ask_for_broad_rewrite
- change_public_api_without_explicit_permission
- weaken_safety_contract
- bypass_human_review
- use_live_external_apis_in_tests

4. Seed data: the thing that makes discovery real

Provide at least 10 labelled examples.

evals/datasets/
small_gold/
manifest.json
cases/_.json
known_plus_unknown/
manifest.json
cases/_.json
adversarial/
manifest.json
cases/_.json
regression_cases/
manifest.json
cases/_.json

Minimum examples:

1. audio-only, 2 known speakers, clean
2. video, 2 known speakers, clear faces
3. video call, 4 known speakers, grid layout
4. panel, 5 speakers, overlapping speech
5. audio-only with one unknown speaker
6. video with off-camera speaker
7. short interjections
8. similar voices
9. poor lighting
10. same person across two media files

A case should look like this:

{
"case_id": "video_call_001",
"media_uri": "s3://dev-datasets/video_call_001.mp4",
"known_people_set_id": "seed_team",
"media_type": "video",
"conditions": {
"speaker_count": 4,
"has_unknown_speakers": false,
"overlap_level": "low",
"face_visibility": "high"
},
"ground_truth": {
"segments": [
{
"segment_id": "seg_001",
"start": 0.82,
"end": 4.91,
"text": "Let's walk through the plan for today.",
"true_person_id": "person_kris",
"speaker_type": "known"
}
]
}
}

Without labelled examples, recursive improvement is fake. Codex will just make plausible changes.

5. The harness needs to produce Codex tasks

Create this command:

uv run python -m app.harness_optimizer.next_task \
 --eval-report evals/reports/latest.json \
 --failure-report evals/failures/latest_failures.json \
 --output prompts/codex_tasks/generated/next_task.md

It should generate a task like this:

# Codex task: reduce false assignment on short voice segments

## Observed failure

`known_plus_unknown` shows false assignments where unknown speakers with short utterances are matched to known registry speakers.

## Affected cases

- panel_003 seg_014
- podcast_002 seg_008
- meeting_007 seg_021

## Suspected cause

Voice KNN currently allows 1-second segments to contribute to final identity assignment.

## Required change

Modify voice evidence scoring so that segments under 2.5 seconds may generate candidates but cannot trigger auto-assignment unless independent face or active-speaker evidence agrees.

## Files likely to change

- app/identity/scoring.py
- app/strategies/voice_knn.py
- tests/golden/test_short_voice_segments.py
- docs/failure_modes.md

## Files not to change

- app/api/routes/results.py
- bootstrap/output_contract.yaml
- bootstrap/safety_contract.yaml

## Acceptance criteria

- Add a regression fixture for short unknown voice segments.
- false_assignment_rate decreases on `known_plus_unknown`.
- unknown_rate may increase by no more than 5%.
- output contract does not change.
- human-reviewed labels remain authoritative.

## Required command

`uv run pytest && uv run python -m evals.run_eval --dataset evals/datasets/known_plus_unknown`

Then give that file to Codex as the task.

That is how recursion starts.

6. What the loop looks like in practice
   Step 1: Human starts the repo

You create:

AGENTS.md
docs/_.md
bootstrap/_.yaml
evals/datasets/small_gold
tests/\*
Step 2: Ask Codex to build the bootstrap loader

Prompt Codex:

Build the bootstrap contract system.

Requirements:

- Read all YAML files from bootstrap/.
- Validate them with Pydantic models.
- Generate app/config/generated_harness_config.json.
- Generate evals/reports/bootstrap_readiness.json.
- Add tests for missing required contracts, invalid tool declarations, and missing output fields.
- Do not call external APIs.
- Update docs/data_contracts.md.
  Step 3: Ask Codex to build the first eval loop
  Implement the first baseline strategy and eval runner.

Requirements:

- Add BaseResolutionStrategy.
- Add BaselineUnknownStrategy.
- Add eval fixture format for labelled transcript segments.
- Add evals.run_eval.
- Report identity_accuracy, false_assignment_rate, unknown_rate, needs_review_rate.
- Add tests with tiny synthetic fixtures.
- Do not integrate Deepgram, pyannote, InsightFace, or real embeddings yet.
  Step 4: Ask Codex to build strategy comparison
  Implement strategy comparison.

Requirements:

- Read bootstrap/strategy_space.yaml.
- Register available strategies.
- Run all compatible strategies against a dataset.
- Select winner under bootstrap/metric_contract.yaml constraints.
- Write evals/reports/strategy_comparison.json.
- Add tests proving that highest raw accuracy does not win if false_assignment_rate violates constraints.
  Step 5: Ask Codex to build task generation
  Implement harness_optimizer.next_task.

Requirements:

- Read evals/reports/latest.json.
- Read evals/failures/latest_failures.json.
- Cluster failures by failure_type, condition, and suspected cause.
- Select the highest-impact failure under metric_contract.yaml.
- Generate prompts/codex_tasks/generated/next_task.md using bootstrap/codex_task_policy.yaml.
- Add tests using fake eval reports.

At this point, you have the recursive loop.

7. CI is the enforcement layer

Add .github/workflows/test-and-eval.yml:

name: test-and-eval

on:
pull_request:
push:
branches: [main]

jobs:
test-and-eval:
runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: uv run ruff check .

      - name: Type check
        run: uv run mypy app evals

      - name: Unit tests
        run: uv run pytest

      - name: Run evals
        run: uv run python -m evals.run_eval --dataset evals/datasets/small_gold

      - name: Check regressions
        run: uv run python -m evals.check_regression --report evals/reports/latest.json

Then turn on Codex review in GitHub and either request @codex review or enable automatic reviews. Codex’s GitHub integration is designed to review PR diffs while following repo guidance such as AGENTS.md.

8. The recursive improvement mechanism

The harness does not recursively improve by editing itself directly.

It recursively improves by generating increasingly good engineering tasks.

1. Run evals.
2. Detect failures.
3. Rank failures by business/safety impact.
4. Generate one narrow Codex task.
5. Codex implements it in a branch.
6. Tests and evals run.
7. Regression guard blocks unsafe changes.
8. Codex reviews the PR.
9. Human reviews and merges.
10. New production/review data expands the eval set.
11. Repeat.

The recursion is in the failure-to-task-to-eval loop, not in unsupervised code mutation.

9. What to commit before asking Codex to do serious work

Commit this first:

AGENTS.md
README.md
docs/architecture.md
docs/codex_workflow.md
docs/data_contracts.md
docs/eval_methodology.md
docs/privacy_security.md

bootstrap/domain_contract.yaml
bootstrap/input_contract.yaml
bootstrap/output_contract.yaml
bootstrap/tool_registry.yaml
bootstrap/strategy_space.yaml
bootstrap/metric_contract.yaml
bootstrap/safety_contract.yaml
bootstrap/dataset_manifest.yaml
bootstrap/codex_task_policy.yaml

evals/datasets/small_gold/manifest.json
evals/datasets/small_gold/cases/\*.json

tests/
pyproject.toml
.github/workflows/test-and-eval.yml

Then Codex has enough context to build rather than guess.

10. The blunt answer

Provide Codex with:

AGENTS.md
Markdown docs
YAML contracts
seed datasets
eval runner
failure reports
task templates
tests
CI gates

Do not just provide:

input schema
output schema
tool calls

That gives you a pipeline.

To get recursive improvement, you need:

input/output/tool contracts

- metric contract
- strategy search space
- labelled evals
- trace schema
- failure miner
- Codex task generator
- regression gates
- PR review

The first real milestone is not “it calls Deepgram and pyannote”.

The first real milestone is:

The harness can run two strategies on labelled fixtures,
show which one is safer,
explain the top failure mode,
and generate a Codex task to improve it.

That is when recursive improvement becomes real.
