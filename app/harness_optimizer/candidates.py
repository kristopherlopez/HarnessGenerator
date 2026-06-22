from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.bootstrap.contracts import load_bootstrap_contracts
from app.harness import HarnessHypothesis, write_harness_config
from app.workspaces import (
    resolve_workspace,
    workspace_codex_task_path,
    workspace_experiment_path,
    workspace_report_path,
)
from evals.reports import write_json

ProposalStatus = Literal["proposed", "rejected"]


class HarnessCandidateProposal(BaseModel):
    candidate_id: str
    title: str
    failure_type: str
    change_surface: str
    change_option: str
    status: ProposalStatus = "proposed"
    rationale: str
    required_change: str
    expected_metric_effect: dict[str, str]
    risk_notes: list[str]
    affected_cases: list[str]
    files_likely_to_change: list[str]
    files_not_to_change: list[str]
    acceptance_criteria: list[str]
    required_commands: list[str]
    safety_checks: list[str]
    harness_hypothesis: HarnessHypothesis
    harness_artifact: str | None = None


class CandidateProposalReport(BaseModel):
    eval_report: str
    failure_report: str
    phase: str
    selected_failure_type: str
    allowed_change_surfaces: list[str]
    proposals: list[HarnessCandidateProposal] = Field(min_length=1)


def propose_candidates(
    eval_report_path: Path,
    failure_report_path: Path,
    output_path: Path | None = None,
    tasks_dir: Path | None = None,
    harnesses_dir: Path | None = None,
    phase: str = "phase_1_fixture_loop",
    max_candidates: int = 3,
    workspace: Path | None = None,
) -> CandidateProposalReport:
    contracts = load_bootstrap_contracts(workspace=workspace)
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    failure_report = json.loads(failure_report_path.read_text(encoding="utf-8"))
    failures = failure_report.get("failures", [])
    selected_failure_type = _select_failure_type(failures)

    allowed_surfaces = contracts.harness_search.staged_unlocks.get(phase)
    if allowed_surfaces is None:
        raise ValueError(f"Unknown harness search phase: {phase}")

    proposals = _build_proposals(
        selected_failure_type=selected_failure_type,
        failures=[
            failure for failure in failures if failure.get("failure_type") == selected_failure_type
        ],
        metrics=eval_report.get("metrics", {}),
        allowed_surfaces=allowed_surfaces,
        max_candidates=max_candidates,
        workspace=workspace,
    )

    report = CandidateProposalReport(
        eval_report=str(eval_report_path),
        failure_report=str(failure_report_path),
        phase=phase,
        selected_failure_type=selected_failure_type,
        allowed_change_surfaces=allowed_surfaces,
        proposals=proposals,
    )

    resolved_output_path = output_path or workspace_report_path(
        workspace,
        "candidate_proposals.json",
        Path("evals/reports/candidate_proposals.json"),
    )
    resolved_tasks_dir = tasks_dir or workspace_codex_task_path(
        workspace,
        "generated",
        "candidates",
        fallback=Path("prompts/codex_tasks/generated/candidates"),
    )
    resolved_harnesses_dir = harnesses_dir or workspace_experiment_path(
        workspace,
        "generated_harnesses",
        fallback=Path("experiments/generated_harnesses"),
    )

    _write_candidate_harnesses(report, resolved_harnesses_dir, workspace)
    write_json(resolved_output_path, report.model_dump())
    _write_candidate_tasks(report, resolved_tasks_dir)
    return report


def _select_failure_type(failures: list[dict[str, Any]]) -> str:
    if not failures:
        return "no_failures"
    priority = {
        "false_assignment": 0,
        "unknown_forced_to_known": 1,
        "missed_known_identity": 2,
    }
    counts: dict[str, int] = {}
    for failure in failures:
        failure_type = str(failure.get("failure_type"))
        counts[failure_type] = counts.get(failure_type, 0) + 1
    return sorted(counts, key=lambda item: (priority.get(item, 99), -counts[item]))[0]


def _build_proposals(
    selected_failure_type: str,
    failures: list[dict[str, Any]],
    metrics: dict[str, Any],
    allowed_surfaces: list[str],
    max_candidates: int,
    workspace: Path | None,
) -> list[HarnessCandidateProposal]:
    if selected_failure_type == "missed_known_identity":
        templates = _missed_known_identity_templates(metrics, workspace)
    elif selected_failure_type in {"false_assignment", "unknown_forced_to_known"}:
        templates = _false_assignment_templates(metrics, workspace)
    else:
        templates = _hardening_templates(metrics, workspace)

    affected_cases = [f"{item['case_id']} {item['segment_id']}" for item in failures[:5]]
    proposals: list[HarnessCandidateProposal] = []
    task_type = _task_type(workspace)
    for template in templates:
        if template["change_surface"] not in allowed_surfaces:
            continue
        proposal_number = len(proposals) + 1
        candidate_id = f"candidate_{proposal_number:03d}"
        proposals.append(
            HarnessCandidateProposal(
                candidate_id=candidate_id,
                failure_type=selected_failure_type,
                affected_cases=affected_cases,
                harness_hypothesis=_candidate_hypothesis(
                    task_type=task_type,
                    candidate_id=candidate_id,
                    selected_failure_type=selected_failure_type,
                    template=template,
                ),
                **template,
            )
        )
        if len(proposals) >= max_candidates:
            break

    if not proposals:
        proposals.append(_fallback_proposal(selected_failure_type, affected_cases, workspace))
    return proposals


def _missed_known_identity_templates(
    metrics: dict[str, Any],
    workspace: Path | None,
) -> list[dict[str, Any]]:
    recall = metrics.get("known_person_recall", "unknown")
    return [
        {
            "title": "Allow high-margin long voice evidence for known speakers",
            "change_surface": "evidence_strategy",
            "change_option": "voice_only_match",
            "rationale": (
                f"Known-person recall is {recall}. Several missed identities have usable "
                "voice evidence but no reliable face signal."
            ),
            "required_change": (
                "Add a conservative voice-only assignment path for known speakers when voice "
                "confidence, duration, and candidate margin are all strong."
            ),
            "expected_metric_effect": {
                "known_person_recall": "increase",
                "false_assignment_rate": "must remain <= configured limit",
                "needs_review_rate": "may decrease slightly",
            },
            "risk_notes": [
                "Could falsely assign unknown speakers with similar voices.",
                "Must keep short utterances blocked from auto-assignment.",
            ],
            "files_likely_to_change": [
                "app/identity/strategies.py",
                "tests/test_compare_strategies.py",
                "datasets/small_gold/cases/video_off_camera.json",
            ],
            "files_not_to_change": [
                "contracts/output_contract.yaml",
                "contracts/safety_contract.yaml",
            ],
            "acceptance_criteria": [
                "Long high-confidence voice-only known-speaker case is resolved.",
                "Short unknown voice interjection remains needs_review or unknown.",
                "false_assignment_rate remains within contract.",
            ],
            "required_commands": _standard_commands(workspace),
            "safety_checks": _standard_safety_checks(),
        },
        {
            "title": "Separate ambiguous voice evidence from weak evidence",
            "change_surface": "verification",
            "change_option": "registry_conflict_check",
            "rationale": (
                "Similar-voice and overlap cases are both becoming unknown, but they represent "
                "different failures. The harness needs clearer verification outcomes."
            ),
            "required_change": (
                "Classify close top-candidate margins as needs_review with conflict provenance "
                "instead of dropping them into generic unknown."
            ),
            "expected_metric_effect": {
                "known_person_recall": "unchanged or slight increase",
                "needs_review_rate": "may increase within limit",
                "failure_report_quality": "increase",
            },
            "risk_notes": [
                "Review rate can rise if too many ambiguous spans are escalated.",
            ],
            "files_likely_to_change": [
                "app/identity/strategies.py",
                "evals/metrics.py",
                "tests/test_eval_runner.py",
            ],
            "files_not_to_change": [
                "contracts/output_contract.yaml",
                "contracts/safety_contract.yaml",
            ],
            "acceptance_criteria": [
                "Similar-voice case is marked needs_review with conflict evidence.",
                "needs_review_rate remains within contract.",
                "Generated failure report distinguishes weak evidence from ambiguity.",
            ],
            "required_commands": _standard_commands(workspace),
            "safety_checks": _standard_safety_checks(),
        },
        {
            "title": "Tune assignment and review thresholds for fixture loop",
            "change_surface": "thresholds_and_policies",
            "change_option": "assignment_threshold",
            "rationale": (
                "The conservative strategy leaves known speakers unresolved even when evidence "
                "is strong enough to evaluate threshold tradeoffs."
            ),
            "required_change": (
                "Move resolver thresholds into a config object and test a tighter policy for "
                "voice duration, confidence, and margin."
            ),
            "expected_metric_effect": {
                "known_person_recall": "increase",
                "known_person_precision": "must remain 1.0 on small_gold",
                "false_assignment_rate": "must remain 0.0 on small_gold",
            },
            "risk_notes": [
                "Threshold tuning can overfit synthetic fixtures.",
                "Thresholds must stay documented and configurable.",
            ],
            "files_likely_to_change": [
                "app/identity/strategies.py",
                "contracts/strategy_space.yaml",
                "docs/resolver_strategies.md",
                "tests/test_compare_strategies.py",
            ],
            "files_not_to_change": [
                "contracts/output_contract.yaml",
                "contracts/safety_contract.yaml",
            ],
            "acceptance_criteria": [
                "Thresholds are not hardcoded in multiple places.",
                "Strategy comparison still rejects risky_top_candidate.",
                "Eval report includes before/after metric impact.",
            ],
            "required_commands": _standard_commands(workspace),
            "safety_checks": _standard_safety_checks(),
        },
    ]


def _false_assignment_templates(
    metrics: dict[str, Any],
    workspace: Path | None,
) -> list[dict[str, Any]]:
    false_assignment_rate = metrics.get("false_assignment_rate", "unknown")
    return [
        {
            "title": "Strengthen short-utterance assignment guard",
            "change_surface": "verification",
            "change_option": "short_utterance_guard",
            "rationale": (
                f"False-assignment rate is {false_assignment_rate}; short spans are high risk."
            ),
            "required_change": (
                "Prevent short voice-only spans from triggering automatic real-person assignment "
                "unless independent face or active-speaker evidence agrees."
            ),
            "expected_metric_effect": {
                "false_assignment_rate": "decrease",
                "needs_review_rate": "may increase within limit",
            },
            "risk_notes": ["Known-person recall may decrease on short valid utterances."],
            "files_likely_to_change": ["app/identity/strategies.py", "tests/"],
            "files_not_to_change": [
                "contracts/output_contract.yaml",
                "contracts/safety_contract.yaml",
            ],
            "acceptance_criteria": [
                "Short unknown voice segments are not auto-assigned.",
                "Regression check passes.",
            ],
            "required_commands": _standard_commands(workspace),
            "safety_checks": _standard_safety_checks(),
        }
    ]


def _hardening_templates(metrics: dict[str, Any], workspace: Path | None) -> list[dict[str, Any]]:
    identity_accuracy = metrics.get("identity_accuracy", "unknown")
    return [
        {
            "title": "Add hardening fixture for current no-failure state",
            "change_surface": "verification",
            "change_option": "contract_compliance_check",
            "rationale": (
                f"Identity accuracy is {identity_accuracy}; no dominant failure was selected."
            ),
            "required_change": "Add a regression fixture that exercises contract compliance.",
            "expected_metric_effect": {"regression_coverage": "increase"},
            "risk_notes": ["No production resolver behavior should change."],
            "files_likely_to_change": ["datasets/small_gold/cases/", "tests/"],
            "files_not_to_change": [
                "contracts/output_contract.yaml",
                "contracts/safety_contract.yaml",
            ],
            "acceptance_criteria": ["New fixture is included in manifest.", "All checks pass."],
            "required_commands": _standard_commands(workspace),
            "safety_checks": _standard_safety_checks(),
        }
    ]


def _fallback_proposal(
    selected_failure_type: str,
    affected_cases: list[str],
    workspace: Path | None,
) -> HarnessCandidateProposal:
    template: dict[str, Any] = {
        "change_surface": "verification",
        "change_option": "contract_compliance_check",
        "required_change": (
            "Add a regression test and failure classification for the selected failure type."
        ),
        "expected_metric_effect": {"regression_coverage": "increase"},
        "risk_notes": ["No resolver behavior should change without a more specific task."],
        "acceptance_criteria": ["All checks pass.", "Failure is represented in tests."],
        "safety_checks": _standard_safety_checks(),
    }
    return HarnessCandidateProposal(
        candidate_id="candidate_001",
        title="Add failure-specific regression coverage",
        failure_type=selected_failure_type,
        change_surface=str(template["change_surface"]),
        change_option=str(template["change_option"]),
        rationale="No phase-compatible proposal template matched the selected failure.",
        required_change=str(template["required_change"]),
        expected_metric_effect=dict(template["expected_metric_effect"]),
        risk_notes=list(template["risk_notes"]),
        affected_cases=affected_cases,
        files_likely_to_change=["tests/", "docs/failure_modes.md"],
        files_not_to_change=["contracts/output_contract.yaml", "contracts/safety_contract.yaml"],
        acceptance_criteria=list(template["acceptance_criteria"]),
        required_commands=_standard_commands(workspace),
        safety_checks=list(template["safety_checks"]),
        harness_hypothesis=_candidate_hypothesis(
            task_type=_task_type(workspace),
            candidate_id="candidate_001",
            selected_failure_type=selected_failure_type,
            template=template,
        ),
    )


def _standard_commands(workspace: Path | None) -> list[str]:
    if workspace is None:
        eval_command = "uv run python -m evals.run_eval --dataset evals/datasets/small_gold"
        compare_command = (
            "uv run python -m evals.compare_strategies --dataset evals/datasets/small_gold"
        )
        regression_command = (
            "uv run python -m evals.check_regression --report evals/reports/latest.json"
        )
    else:
        workspace_text = workspace.as_posix()
        eval_command = (
            f"uv run python -m evals.run_eval --workspace {workspace_text} --dataset small_gold"
        )
        compare_command = (
            "uv run python -m evals.compare_strategies "
            f"--workspace {workspace_text} --dataset small_gold"
        )
        regression_command = (
            f"uv run python -m evals.check_regression --workspace {workspace_text}"
        )

    return [
        "uv run pytest",
        "uv run ruff check .",
        "uv run mypy app evals",
        eval_command,
        compare_command,
        regression_command,
    ]


def _standard_safety_checks() -> list[str]:
    return [
        "No identity assignment without evidence provenance.",
        "No live external APIs in tests.",
        "No public exposure of biometric internals.",
        "Human-reviewed labels remain authoritative.",
    ]


def _write_candidate_tasks(report: CandidateProposalReport, tasks_dir: Path) -> None:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for proposal in report.proposals:
        path = tasks_dir / f"{proposal.candidate_id}.md"
        path.write_text(_render_candidate_task(proposal), encoding="utf-8")


def _write_candidate_harnesses(
    report: CandidateProposalReport,
    harnesses_dir: Path,
    workspace: Path | None,
) -> None:
    workspace_id = _task_type(workspace)
    for proposal in report.proposals:
        path = harnesses_dir / proposal.candidate_id / "harness.yaml"
        payload = _harness_config_for_proposal(proposal, workspace_id)
        write_harness_config(path, payload)
        proposal.harness_artifact = path.as_posix()


def _harness_config_for_proposal(
    proposal: HarnessCandidateProposal,
    workspace_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 0.1,
        "harness_id": proposal.candidate_id,
        "workspace_id": workspace_id,
        "status": "generated_candidate",
        "strategy": "review_heavy_low_false_assignment",
        "strategy_type": "conservative_evidence",
        "parent": "review_heavy_low_false_assignment",
        "change_surface": proposal.change_surface,
        "change_option": proposal.change_option,
        "description": proposal.title,
        "resolver_config": _resolver_config_for_proposal(proposal),
        "candidate": {
            "failure_type": proposal.failure_type,
            "rationale": proposal.rationale,
            "required_change": proposal.required_change,
            "affected_cases": proposal.affected_cases,
            "risk_notes": proposal.risk_notes,
        },
        "contracts": {
            "output": "../../contracts/output_contract.yaml",
            "safety": "../../contracts/safety_contract.yaml",
            "metrics": "../../contracts/metric_contract.yaml",
        },
        "expected_behavior": proposal.expected_metric_effect,
    }


def _resolver_config_for_proposal(proposal: HarnessCandidateProposal) -> dict[str, Any]:
    config: dict[str, Any] = {
        "assignment_threshold": 0.85,
        "voice_only_assignment_threshold": 0.80,
        "review_threshold": 0.60,
        "max_review_rate": 0.25,
        "minimum_review_slots": 1,
        "overlap_handling_policy": "require_corroborating_signal_on_high_overlap",
        "high_overlap_levels": ["high"],
        "margin_threshold": 0.08,
        "voice_only_margin_threshold": 0.10,
        "min_voice_duration_seconds": 2.5,
        "min_voice_only_duration_seconds": 5.0,
        "ambiguous_voice_conflict_status": "needs_review",
    }
    if proposal.change_option == "voice_only_match":
        config["voice_only_margin_threshold"] = 0.15
        config["min_voice_only_duration_seconds"] = 3.0
    elif proposal.change_option == "registry_conflict_check":
        config["voice_only_margin_threshold"] = 0.15
    elif proposal.change_option == "assignment_threshold":
        config["assignment_threshold"] = 0.90
        config["margin_threshold"] = 0.10
    elif proposal.change_option == "short_utterance_guard":
        config["min_voice_duration_seconds"] = 3.0
        config["min_voice_only_duration_seconds"] = 6.0
    return config


def _render_candidate_task(proposal: HarnessCandidateProposal) -> str:
    return f"""# Codex Task: {proposal.title}

## Observed Failure

Selected failure type: `{proposal.failure_type}`.

## Affected Cases

{_format_bullets(proposal.affected_cases)}

## Harness Change Surface

- Surface: `{proposal.change_surface}`
- Option: `{proposal.change_option}`

## Harness Hypothesis

- Harness: `{proposal.harness_hypothesis.harness_id}`
- Version: `{proposal.harness_hypothesis.version}`
- Change surface: `{proposal.harness_hypothesis.declared_change_surface}`
- Runnable config: `{proposal.harness_artifact or "not materialized"}`

## Rationale

{proposal.rationale}

## Required Change

{proposal.required_change}

## Expected Metric Effect

{_format_key_values(proposal.expected_metric_effect)}

## Risk Notes

{_format_bullets(proposal.risk_notes)}

## Files Likely To Change

{_format_bullets(proposal.files_likely_to_change)}

## Files Not To Change

{_format_bullets(proposal.files_not_to_change)}

## Acceptance Criteria

{_format_bullets(proposal.acceptance_criteria)}

## Required Commands

{_format_code_bullets(proposal.required_commands)}

## Safety Checks

{_format_bullets(proposal.safety_checks)}
"""


def _format_bullets(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def _format_key_values(items: dict[str, str]) -> str:
    return "\n".join(f"- `{key}`: {value}" for key, value in items.items())


def _format_code_bullets(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items)


def _candidate_hypothesis(
    *,
    task_type: str,
    candidate_id: str,
    selected_failure_type: str,
    template: dict[str, Any],
) -> HarnessHypothesis:
    return HarnessHypothesis(
        harness_id=f"{task_type}:{candidate_id}",
        version="candidate-hypothesis-v1",
        task_type=task_type,
        declared_change_surface=str(template["change_surface"]),
        decomposition_steps=[
            "apply_candidate_change",
            "run_harness_api",
            "validate_output",
            "score_against_gold",
        ],
        verification_checks=list(template["acceptance_criteria"]),
        retry_policy={"max_retries": 0},
        stopping_rules=["stop_after_scored_eval"],
        confidence_policy={"expected_metric_effect": template["expected_metric_effect"]},
        review_policy={"safety_checks": template["safety_checks"]},
        expected_budget_impact={
            "model_calls": "unchanged unless candidate explicitly changes provider routing",
            "tool_calls": "unchanged unless candidate explicitly changes tool policy",
        },
        config={
            "failure_type": selected_failure_type,
            "change_option": template["change_option"],
            "required_change": template["required_change"],
            "risk_notes": template["risk_notes"],
        },
    )


def _task_type(workspace: Path | None) -> str:
    return workspace.name if workspace is not None else "generic"


def main() -> None:
    parser = argparse.ArgumentParser(description="Propose bounded harness candidate changes.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--eval-report", type=Path)
    parser.add_argument("--failure-report", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
    )
    parser.add_argument(
        "--harnesses-dir",
        type=Path,
    )
    parser.add_argument("--phase", default="phase_1_fixture_loop")
    parser.add_argument("--max-candidates", default=3, type=int)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    eval_report = args.eval_report or workspace_report_path(
        workspace,
        "latest.json",
        Path("evals/reports/latest.json"),
    )
    failure_report = args.failure_report or workspace_report_path(
        workspace,
        "latest_failures.json",
        Path("evals/failures/latest_failures.json"),
    )

    propose_candidates(
        eval_report_path=eval_report,
        failure_report_path=failure_report,
        output_path=args.output,
        tasks_dir=args.tasks_dir,
        harnesses_dir=args.harnesses_dir,
        phase=args.phase,
        max_candidates=args.max_candidates,
        workspace=workspace,
    )


if __name__ == "__main__":
    main()
