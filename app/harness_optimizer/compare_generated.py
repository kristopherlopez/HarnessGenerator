from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.bootstrap.contracts import load_bootstrap_contracts
from app.harness import load_harness_config
from app.workspaces import resolve_workspace, workspace_report_path
from evals.reports import write_json

QUALITY_METRICS = ("identity_accuracy", "known_person_recall", "exact_match")
SAFETY_METRICS = ("false_assignment_rate", "needs_review_rate", "malformed_output_rate")
EPSILON = 1e-9


def compare_generated_candidates(
    *,
    baseline_report_path: Path,
    candidate_report_paths: list[Path],
    output_path: Path,
    workspace: Path | None = None,
    outcomes_output_path: Path | None = None,
    outcomes_markdown_output_path: Path | None = None,
) -> dict[str, Any]:
    contracts = load_bootstrap_contracts(workspace=workspace)
    baseline = _load_report(baseline_report_path)
    candidates = [_load_report(path) for path in candidate_report_paths]
    constraints = contracts.strategy.selection_policy.get("constraints", {})
    baseline_failure_report = _load_failure_report_for(baseline_report_path, baseline)
    candidate_failure_reports = [
        _load_failure_report_for(path, report)
        for path, report in zip(candidate_report_paths, candidates, strict=True)
    ]

    baseline_summary = _summary(baseline_report_path, baseline, constraints, baseline=None)
    candidate_summaries = [
        _summary(path, report, constraints, baseline=baseline_summary)
        for path, report in zip(candidate_report_paths, candidates, strict=True)
    ]
    eligible_candidates = [candidate for candidate in candidate_summaries if candidate["eligible"]]
    winner = _select_winner(eligible_candidates)
    decision = _decision(baseline_summary, winner)
    outcome_report = _build_outcome_report(
        baseline=baseline_summary,
        candidates=candidate_summaries,
        baseline_failure_report=baseline_failure_report,
        candidate_failure_reports=candidate_failure_reports,
        constraints=constraints,
        winner=winner,
        decision=decision,
    )
    report = {
        "baseline": baseline_summary,
        "candidates": candidate_summaries,
        "winner": winner["strategy"] if winner else None,
        "decision": decision,
        "selection_policy": contracts.strategy.selection_policy,
        "candidate_outcomes": outcome_report["candidates"],
    }
    if outcomes_output_path is not None:
        write_json(outcomes_output_path, outcome_report)
        report["outcome_report_path"] = outcomes_output_path.as_posix()
    if outcomes_markdown_output_path is not None:
        _write_outcomes_markdown(outcomes_markdown_output_path, outcome_report)
        report["outcome_markdown_path"] = outcomes_markdown_output_path.as_posix()
    write_json(output_path, report)
    return report


def _load_report(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def _summary(
    path: Path,
    report: dict[str, Any],
    constraints: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = _metrics(report)
    return {
        "path": path.as_posix(),
        "strategy": str(report.get("strategy", path.stem)),
        "harness_config_path": report.get("harness_config_path"),
        "harness_component": _harness_component(report),
        "metrics": metrics,
        "eligible": _eligible(metrics, constraints),
        "delta_from_baseline": _delta(metrics, baseline["metrics"]) if baseline else {},
        "harness_run_summary": report.get("harness_run_summary", {}),
    }


def _harness_component(report: dict[str, Any]) -> dict[str, Any]:
    config = _harness_config_from_report(report)
    config_path = report.get("harness_config_path")
    if isinstance(config_path, str | Path) and str(config_path):
        path = Path(config_path)
        if path.exists():
            config = load_harness_config(path)

    hypothesis = report.get("harness_hypothesis", {})
    if not isinstance(hypothesis, dict):
        hypothesis = {}
    candidate = config.get("candidate", {})
    if not isinstance(candidate, dict):
        candidate = {}

    return {
        "harness_id": config.get("harness_id") or report.get("strategy"),
        "parent": config.get("parent"),
        "change_surface": config.get("change_surface")
        or hypothesis.get("declared_change_surface"),
        "change_option": config.get("change_option"),
        "description": config.get("description"),
        "failure_type": candidate.get("failure_type"),
        "required_change": candidate.get("required_change"),
        "rationale": candidate.get("rationale"),
        "affected_cases": candidate.get("affected_cases", []),
        "risk_notes": candidate.get("risk_notes", []),
        "expected_behavior": config.get("expected_behavior", {}),
        "resolver_config": config.get("resolver_config", {}),
    }


def _harness_config_from_report(report: dict[str, Any]) -> dict[str, Any]:
    hypothesis = report.get("harness_hypothesis", {})
    if not isinstance(hypothesis, dict):
        return {}
    config = hypothesis.get("config", {})
    return config if isinstance(config, dict) else {}


def _metrics(report: dict[str, Any]) -> dict[str, float]:
    raw_metrics = report.get("metrics", {})
    if not isinstance(raw_metrics, dict):
        raise ValueError("report metrics must be a JSON object")
    metrics: dict[str, float] = {}
    for key, value in raw_metrics.items():
        if isinstance(value, int | float):
            metrics[str(key)] = float(value)
    return metrics


def _eligible(metrics: dict[str, float], constraints: dict[str, Any]) -> bool:
    max_false_assignment = float(constraints.get("max_false_assignment_rate", 1.0))
    max_review = float(constraints.get("max_review_rate", 1.0))
    max_malformed = float(constraints.get("max_malformed_output_rate", 1.0))
    return (
        metrics.get("false_assignment_rate", 0.0) <= max_false_assignment
        and metrics.get("needs_review_rate", 0.0) <= max_review
        and metrics.get("malformed_output_rate", 0.0) <= max_malformed
    )


def _delta(
    metrics: dict[str, float],
    baseline_metrics: dict[str, float],
) -> dict[str, float]:
    return {
        key: metrics[key] - baseline_metrics[key]
        for key in sorted(metrics.keys() & baseline_metrics.keys())
    }


def _select_winner(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["metrics"].get("false_assignment_rate", 0.0),
            -_best_quality(candidate["metrics"]),
            candidate["metrics"].get("needs_review_rate", 0.0),
            candidate["strategy"],
        ),
    )[0]


def _decision(
    baseline: dict[str, Any],
    winner: dict[str, Any] | None,
) -> dict[str, Any]:
    if winner is None:
        return {
            "action": "reject",
            "recommendation": "generate_follow_up",
            "rationale": "No generated candidate satisfied the workspace constraints.",
        }
    if _improves_on_baseline(winner["metrics"], baseline["metrics"]):
        return {
            "action": "accept",
            "recommendation": "promote_candidate",
            "rationale": (
                f"{winner['strategy']} is eligible and improves quality metrics without "
                "weakening configured safety constraints."
            ),
        }
    return {
        "action": "reject",
        "recommendation": "generate_follow_up",
        "rationale": (
            f"{winner['strategy']} is eligible but does not improve on the promoted baseline."
        ),
    }


def _improves_on_baseline(
    metrics: dict[str, float],
    baseline: dict[str, float],
) -> bool:
    false_assignment_delta = (
        metrics.get("false_assignment_rate", 0.0)
        - baseline.get("false_assignment_rate", 0.0)
    )
    review_delta = metrics.get("needs_review_rate", 0.0) - baseline.get("needs_review_rate", 0.0)
    if false_assignment_delta > 0.0 or review_delta > 0.0:
        return False
    return any(metrics.get(key, 0.0) > baseline.get(key, 0.0) for key in QUALITY_METRICS)


def _best_quality(metrics: dict[str, float]) -> float:
    return max((metrics.get(key, 0.0) for key in QUALITY_METRICS), default=0.0)


def _build_outcome_report(
    *,
    baseline: dict[str, Any],
    candidates: list[dict[str, Any]],
    baseline_failure_report: dict[str, Any],
    candidate_failure_reports: list[dict[str, Any]],
    constraints: dict[str, Any],
    winner: dict[str, Any] | None,
    decision: dict[str, Any],
) -> dict[str, Any]:
    outcome_summaries = [
        _candidate_outcome(
            baseline=baseline,
            candidate=candidate,
            baseline_failure_report=baseline_failure_report,
            candidate_failure_report=failure_report,
            constraints=constraints,
            is_winner=winner is not None and winner["strategy"] == candidate["strategy"],
        )
        for candidate, failure_report in zip(
            candidates, candidate_failure_reports, strict=True
        )
    ]
    return {
        "schema_version": 1,
        "baseline": {
            "strategy": baseline["strategy"],
            "report_path": baseline["path"],
            "failure_report_path": baseline_failure_report.get("path"),
            "metrics": baseline["metrics"],
            "failure_count": baseline_failure_report["failure_count"],
            "by_failure_type": baseline_failure_report["by_failure_type"],
        },
        "candidates": outcome_summaries,
        "winner": winner["strategy"] if winner else None,
        "decision": decision,
    }


def _candidate_outcome(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    baseline_failure_report: dict[str, Any],
    candidate_failure_report: dict[str, Any],
    constraints: dict[str, Any],
    is_winner: bool,
) -> dict[str, Any]:
    failure_delta = _failure_delta(
        baseline_failure_report["failures"],
        candidate_failure_report["failures"],
    )
    prediction_checks = _prediction_checks(
        expected_behavior=candidate["harness_component"].get("expected_behavior", {}),
        candidate=candidate,
        baseline=baseline,
        failure_delta=failure_delta,
        constraints=constraints,
    )
    prediction_verdict = _prediction_verdict(prediction_checks)
    outcome = _outcome_classification(candidate, baseline, failure_delta)
    why = _outcome_rationale(candidate, baseline, failure_delta, prediction_verdict, outcome)
    return {
        "candidate_id": candidate["strategy"],
        "report_path": candidate["path"],
        "harness_config_path": candidate.get("harness_config_path"),
        "component": candidate["harness_component"],
        "is_winner": is_winner,
        "eligible": candidate["eligible"],
        "metrics": candidate["metrics"],
        "delta_from_baseline": candidate["delta_from_baseline"],
        "predicted_effect": candidate["harness_component"].get("expected_behavior", {}),
        "prediction_checks": prediction_checks,
        "prediction_verdict": prediction_verdict,
        "outcome": outcome,
        "decision": "promote" if outcome == "success" else "reject",
        "why": why,
        "failure_report_path": candidate_failure_report.get("path"),
        "failure_count": candidate_failure_report["failure_count"],
        "failure_count_delta": (
            candidate_failure_report["failure_count"]
            - baseline_failure_report["failure_count"]
        ),
        "remaining_failures": failure_delta["remaining_failures"],
        "fixed_failures": failure_delta["fixed_failures"],
        "new_failures": failure_delta["new_failures"],
        "changed_failures": failure_delta["changed_failures"],
        "next_recommendation": _next_recommendation(
            candidate,
            failure_delta,
            outcome,
            prediction_verdict,
        ),
    }


def _load_failure_report_for(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    path = _failure_report_path(report_path, report)
    if path is None or not path.exists():
        return {
            "path": path.as_posix() if path is not None else None,
            "failure_count": 0,
            "by_failure_type": {},
            "failures": [],
        }
    loaded = _load_report(path)
    failures = loaded.get("failures", [])
    if not isinstance(failures, list):
        raise ValueError(f"{path} failures must be a JSON array")
    return {
        "path": path.as_posix(),
        "failure_count": int(loaded.get("failure_count", len(failures))),
        "by_failure_type": loaded.get("by_failure_type", {}),
        "failures": [failure for failure in failures if isinstance(failure, dict)],
    }


def _failure_report_path(report_path: Path, report: dict[str, Any]) -> Path | None:
    explicit = report.get("failure_report_path")
    if isinstance(explicit, str | Path) and str(explicit):
        return Path(explicit)
    inferred = report_path.with_name(f"{report_path.stem}_failures.json")
    if inferred.exists():
        return inferred
    latest = report_path.with_name("latest_failures.json")
    if report_path.stem == "latest" and latest.exists():
        return latest
    return None


def _failure_delta(
    baseline_failures: list[dict[str, Any]],
    candidate_failures: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_key = {_failure_key(failure): failure for failure in baseline_failures}
    candidate_by_key = {_failure_key(failure): failure for failure in candidate_failures}

    baseline_keys = set(baseline_by_key)
    candidate_keys = set(candidate_by_key)
    fixed_keys = baseline_keys - candidate_keys
    new_keys = candidate_keys - baseline_keys
    remaining_keys = baseline_keys & candidate_keys
    changed = [
        {
            "before": _failure_digest(baseline_by_key[key]),
            "after": _failure_digest(candidate_by_key[key]),
        }
        for key in sorted(remaining_keys)
        if _failure_digest(baseline_by_key[key]) != _failure_digest(candidate_by_key[key])
    ]

    return {
        "fixed_failures": [
            _failure_digest(baseline_by_key[key]) for key in sorted(fixed_keys)
        ],
        "new_failures": [
            _failure_digest(candidate_by_key[key]) for key in sorted(new_keys)
        ],
        "remaining_failures": [
            _failure_digest(candidate_by_key[key]) for key in sorted(remaining_keys)
        ],
        "changed_failures": changed,
    }


def _failure_key(failure: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(failure.get("case_id", "")),
        str(failure.get("segment_id", "")),
        str(failure.get("failure_type", "")),
    )


def _failure_digest(failure: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": failure.get("case_id"),
        "segment_id": failure.get("segment_id"),
        "failure_type": failure.get("failure_type"),
        "resolution_status": failure.get("resolution_status"),
        "review_reason": failure.get("review_reason"),
        "suspected_cause": failure.get("suspected_cause"),
    }


def _prediction_checks(
    *,
    expected_behavior: dict[str, Any],
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    failure_delta: dict[str, Any],
    constraints: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if not isinstance(expected_behavior, dict):
        return checks
    for metric, expectation in expected_behavior.items():
        metric_name = str(metric)
        expectation_text = str(expectation)
        if metric_name == "failure_report_quality":
            checks.append(
                _failure_report_quality_check(expectation_text, failure_delta)
            )
            continue
        if metric_name not in candidate["metrics"]:
            checks.append(
                {
                    "metric": metric_name,
                    "expected": expectation_text,
                    "status": "not_measured",
                    "required": False,
                    "actual": None,
                    "delta_from_baseline": None,
                    "evidence": "Metric was not present in the eval report.",
                }
            )
            continue
        actual = candidate["metrics"][metric_name]
        baseline_value = baseline["metrics"].get(metric_name)
        delta = actual - baseline_value if baseline_value is not None else None
        checks.append(
            _metric_prediction_check(
                metric=metric_name,
                expectation=expectation_text,
                actual=actual,
                delta=delta,
                constraints=constraints,
            )
        )
    return checks


def _failure_report_quality_check(
    expectation: str,
    failure_delta: dict[str, Any],
) -> dict[str, Any]:
    fixed_count = len(failure_delta["fixed_failures"])
    changed_count = len(failure_delta["changed_failures"])
    new_count = len(failure_delta["new_failures"])
    improved = (fixed_count > 0 or changed_count > 0) and new_count == 0
    return {
        "metric": "failure_report_quality",
        "expected": expectation,
        "status": "passed" if improved else "failed",
        "required": "increase" in expectation.lower(),
        "actual": {
            "fixed_failure_count": fixed_count,
            "changed_failure_count": changed_count,
            "new_failure_count": new_count,
        },
        "delta_from_baseline": None,
        "evidence": (
            "Failure report changed without introducing new failures."
            if improved
            else "Failure report did not improve the persistent failure evidence."
        ),
    }


def _metric_prediction_check(
    *,
    metric: str,
    expectation: str,
    actual: float,
    delta: float | None,
    constraints: dict[str, Any],
) -> dict[str, Any]:
    expectation_lower = expectation.lower()
    required = not expectation_lower.startswith("may ")
    status = "not_measured"
    evidence = "Expectation was recorded but no directional rule matched."

    if "must remain <=" in expectation_lower or "within limit" in expectation_lower:
        limit = _constraint_limit(metric, constraints)
        passed = True if limit is None else actual <= limit + EPSILON
        status = "passed" if passed else "failed"
        evidence = (
            f"{metric}={actual} stayed within configured limit {limit}."
            if passed
            else f"{metric}={actual} exceeded configured limit {limit}."
        )
    elif "must remain 0.0" in expectation_lower:
        status = "passed" if abs(actual) <= EPSILON else "failed"
        evidence = f"{metric}={actual}; expected 0.0."
    elif "must remain 1.0" in expectation_lower:
        status = "passed" if abs(actual - 1.0) <= EPSILON else "failed"
        evidence = f"{metric}={actual}; expected 1.0."
    elif "unchanged or slight increase" in expectation_lower:
        passed = delta is None or delta >= -EPSILON
        status = "passed" if passed else "failed"
        evidence = f"{metric} delta was {_format_delta(delta)}."
    elif "increase" in expectation_lower:
        passed = delta is not None and delta > EPSILON
        status = "passed" if passed else "failed"
        evidence = f"{metric} delta was {_format_delta(delta)}."
    elif "decrease" in expectation_lower:
        passed = delta is not None and delta < -EPSILON
        status = "passed" if passed else ("informational" if not required else "failed")
        evidence = f"{metric} delta was {_format_delta(delta)}."

    return {
        "metric": metric,
        "expected": expectation,
        "status": status,
        "required": required,
        "actual": actual,
        "delta_from_baseline": delta,
        "evidence": evidence,
    }


def _constraint_limit(metric: str, constraints: dict[str, Any]) -> float | None:
    lookup = {
        "false_assignment_rate": "max_false_assignment_rate",
        "needs_review_rate": "max_review_rate",
        "malformed_output_rate": "max_malformed_output_rate",
    }
    key = lookup.get(metric)
    if key is None or key not in constraints:
        return None
    return float(constraints[key])


def _prediction_verdict(checks: list[dict[str, Any]]) -> str:
    required = [check for check in checks if check.get("required")]
    if any(check["status"] == "failed" for check in required):
        return "falsified"
    if any(check["status"] == "passed" for check in required):
        return "verified"
    if checks:
        return "inconclusive"
    return "not_declared"


def _outcome_classification(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    failure_delta: dict[str, Any],
) -> str:
    if not candidate["eligible"]:
        return "failure"
    deltas = candidate["delta_from_baseline"]
    if any(deltas.get(metric, 0.0) > EPSILON for metric in SAFETY_METRICS):
        return "regression"
    if any(deltas.get(metric, 0.0) < -EPSILON for metric in QUALITY_METRICS):
        return "regression"
    if len(failure_delta["new_failures"]) > len(failure_delta["fixed_failures"]):
        return "regression"
    if _improves_on_baseline(candidate["metrics"], baseline["metrics"]):
        return "success"
    return "failure"


def _outcome_rationale(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    failure_delta: dict[str, Any],
    prediction_verdict: str,
    outcome: str,
) -> str:
    if outcome == "success":
        return "Candidate improved quality metrics without weakening configured safety metrics."
    if outcome == "regression":
        return _regression_rationale(candidate, failure_delta)
    if not candidate["eligible"]:
        return "Candidate violated the configured selection policy constraints."
    if _all_zero(candidate["delta_from_baseline"]):
        return (
            "Candidate produced the same metrics as the baseline and left the same "
            "failures unresolved."
        )
    if prediction_verdict == "falsified":
        return "Candidate did not produce its declared expected metric effect."
    return (
        f"Candidate did not improve on {baseline['strategy']} enough to justify promotion."
    )


def _regression_rationale(
    candidate: dict[str, Any],
    failure_delta: dict[str, Any],
) -> str:
    deltas = candidate["delta_from_baseline"]
    quality_regressions = [
        f"{metric} {deltas[metric]:+.6f}"
        for metric in QUALITY_METRICS
        if deltas.get(metric, 0.0) < -EPSILON
    ]
    safety_regressions = [
        f"{metric} {deltas[metric]:+.6f}"
        for metric in SAFETY_METRICS
        if deltas.get(metric, 0.0) > EPSILON
    ]
    details = quality_regressions + safety_regressions
    if failure_delta["new_failures"]:
        details.append(f"{len(failure_delta['new_failures'])} new failure(s)")
    if not details:
        return "Candidate regressed relative to the baseline."
    return "Candidate regressed: " + "; ".join(details) + "."


def _next_recommendation(
    candidate: dict[str, Any],
    failure_delta: dict[str, Any],
    outcome: str,
    prediction_verdict: str,
) -> str:
    component = candidate["harness_component"]
    change_option = component.get("change_option") or candidate["strategy"]
    remaining = _failure_targets(failure_delta["remaining_failures"])
    if outcome == "success":
        return (
            f"Promote {candidate['strategy']} only after regression and contract checks "
            "remain clean on the current gold set."
        )
    if failure_delta["new_failures"]:
        new_targets = _failure_targets(failure_delta["new_failures"])
        return (
            f"Reject {candidate['strategy']} and narrow or revert `{change_option}`; "
            f"it introduced new failures on {new_targets}."
        )
    if _all_zero(candidate["delta_from_baseline"]):
        return (
            f"Reject {candidate['strategy']} as a no-op. The next loop should target "
            f"the persistent failure evidence directly: {remaining}."
        )
    if prediction_verdict == "falsified":
        return (
            f"Revise `{change_option}` or its expected effect before retrying; the "
            "declared hypothesis was falsified by the eval."
        )
    return (
        f"Generate a follow-up candidate that changes a different component surface "
        f"than `{change_option}` and measures impact on {remaining}."
    )


def _failure_targets(failures: list[dict[str, Any]]) -> str:
    if not failures:
        return "no remaining failures"
    return ", ".join(
        f"{failure.get('case_id')}#{failure.get('segment_id')}:{failure.get('failure_type')}"
        for failure in failures[:5]
    )


def _all_zero(deltas: dict[str, float]) -> bool:
    return all(abs(value) <= EPSILON for value in deltas.values())


def _format_delta(delta: float | None) -> str:
    if delta is None:
        return "not available"
    return f"{delta:+.6f}"


def _write_outcomes_markdown(path: Path, outcome_report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_outcomes_markdown(outcome_report), encoding="utf-8")
    return path


def _render_outcomes_markdown(outcome_report: dict[str, Any]) -> str:
    lines = [
        "# Generated Candidate Outcomes",
        "",
        f"Winner: `{outcome_report.get('winner')}`",
        f"Decision: `{outcome_report['decision']['action']}` - "
        f"{outcome_report['decision']['rationale']}",
        "",
    ]
    for candidate in outcome_report["candidates"]:
        component = candidate["component"]
        lines.extend(
            [
                f"## {candidate['candidate_id']} - {candidate['outcome']}",
                "",
                f"- Component: `{component.get('change_surface')}` / "
                f"`{component.get('change_option')}`",
                f"- Prediction: `{candidate['prediction_verdict']}`",
                f"- Failure delta: {candidate['failure_count_delta']:+d}",
                f"- Why: {candidate['why']}",
                f"- Next: {candidate['next_recommendation']}",
                "",
            ]
        )
        if candidate["remaining_failures"]:
            lines.append("Remaining failures:")
            for failure in candidate["remaining_failures"]:
                lines.append(
                    f"- `{failure['case_id']}#{failure['segment_id']}` "
                    f"{failure['failure_type']}: {failure['suspected_cause']}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _default_candidate_reports(workspace: Path | None, pattern: str) -> list[Path]:
    root = workspace_report_path(workspace, "", Path("evals/reports"))
    if root.name == "":
        root = root.parent
    return sorted(root.glob(pattern))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare generated harness candidate evals.")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--baseline-report", type=Path)
    parser.add_argument("--candidate-report", type=Path, action="append")
    parser.add_argument(
        "--candidate-report-glob",
        default="generated_candidate_[0-9][0-9][0-9].json",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--outcomes-output", type=Path)
    parser.add_argument("--outcomes-markdown-output", type=Path)
    parser.add_argument("--no-outcomes", action="store_true")
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    baseline_report = args.baseline_report or workspace_report_path(
        workspace,
        "latest.json",
        Path("evals/reports/latest.json"),
    )
    candidate_reports = args.candidate_report or _default_candidate_reports(
        workspace,
        args.candidate_report_glob,
    )
    if not candidate_reports:
        raise SystemExit("No generated candidate reports found.")
    output = args.output or workspace_report_path(
        workspace,
        "generated_candidate_comparison.json",
        Path("evals/reports/generated_candidate_comparison.json"),
    )
    outcomes_output = None
    outcomes_markdown_output = None
    if not args.no_outcomes:
        outcomes_output = args.outcomes_output or workspace_report_path(
            workspace,
            "generated_candidate_outcomes.json",
            Path("evals/reports/generated_candidate_outcomes.json"),
        )
        outcomes_markdown_output = args.outcomes_markdown_output or workspace_report_path(
            workspace,
            "generated_candidate_outcomes.md",
            Path("evals/reports/generated_candidate_outcomes.md"),
        )
    compare_generated_candidates(
        baseline_report_path=baseline_report,
        candidate_report_paths=candidate_reports,
        output_path=output,
        workspace=workspace,
        outcomes_output_path=outcomes_output,
        outcomes_markdown_output_path=outcomes_markdown_output,
    )


if __name__ == "__main__":
    main()
