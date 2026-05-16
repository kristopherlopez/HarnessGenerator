from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.identity.models import (
    CasePrediction,
    EvalCase,
    EvidenceCandidate,
    EvidenceSummary,
    ReviewState,
    SegmentCase,
    SegmentPrediction,
)


class ResolutionStrategy(Protocol):
    name: str

    def predict_case(self, case: EvalCase) -> CasePrediction:
        """Resolve identities for one eval case."""


def _unknown_prediction(segment: SegmentCase, strategy_name: str, reason: str) -> SegmentPrediction:
    return SegmentPrediction(
        segment_id=segment.segment_id,
        start=segment.start,
        end=segment.end,
        text=segment.text,
        speaker_id=f"{strategy_name}_{segment.segment_id}",
        person_id="unknown",
        display_name="Unknown Speaker",
        confidence=0.0,
        resolution_status="unknown",
        evidence_summary=EvidenceSummary(
            evidence_types=[],
            strongest_signal="none",
            provenance=[],
            conflicts=[],
        ),
        review=ReviewState(required=False, reason=reason),
    )


def _resolved_prediction(
    segment: SegmentCase,
    strategy_name: str,
    candidate: EvidenceCandidate,
) -> SegmentPrediction:
    return SegmentPrediction(
        segment_id=segment.segment_id,
        start=segment.start,
        end=segment.end,
        text=segment.text,
        speaker_id=f"{strategy_name}_{segment.segment_id}",
        person_id=candidate.person_id,
        display_name=candidate.display_name,
        confidence=candidate.confidence,
        resolution_status="resolved",
        evidence_summary=EvidenceSummary(
            evidence_types=candidate.evidence_types,
            strongest_signal=candidate.evidence_types[0] if candidate.evidence_types else "unknown",
            provenance=candidate.provenance,
            conflicts=[],
        ),
        review=ReviewState(required=False, reason="assignment_threshold_met"),
    )


def _review_prediction(
    segment: SegmentCase,
    strategy_name: str,
    candidate: EvidenceCandidate | None,
    reason: str,
) -> SegmentPrediction:
    return SegmentPrediction(
        segment_id=segment.segment_id,
        start=segment.start,
        end=segment.end,
        text=segment.text,
        speaker_id=f"{strategy_name}_{segment.segment_id}",
        person_id="unknown",
        display_name="Needs Review",
        confidence=candidate.confidence if candidate else 0.0,
        resolution_status="needs_review",
        evidence_summary=EvidenceSummary(
            evidence_types=candidate.evidence_types if candidate else [],
            strongest_signal=(
                candidate.evidence_types[0] if candidate and candidate.evidence_types else "none"
            ),
            provenance=candidate.provenance if candidate else [],
            conflicts=[reason],
        ),
        review=ReviewState(required=True, reason=reason),
    )


@dataclass(frozen=True)
class BaselineUnknownStrategy(ResolutionStrategy):
    name: str = "baseline_unknown"

    def predict_case(self, case: EvalCase) -> CasePrediction:
        return CasePrediction(
            case_id=case.case_id,
            strategy=self.name,
            segments=[
                _unknown_prediction(segment, self.name, "baseline_never_assigns_identity")
                for segment in case.segments
            ],
        )


@dataclass(frozen=True)
class RiskyTopCandidateStrategy(ResolutionStrategy):
    name: str = "risky_top_candidate"

    def predict_case(self, case: EvalCase) -> CasePrediction:
        predictions: list[SegmentPrediction] = []
        for segment in case.segments:
            if not segment.evidence_candidates:
                predictions.append(_unknown_prediction(segment, self.name, "no_candidate"))
                continue
            candidate = max(segment.evidence_candidates, key=lambda item: item.confidence)
            predictions.append(_resolved_prediction(segment, self.name, candidate))
        return CasePrediction(case_id=case.case_id, strategy=self.name, segments=predictions)


@dataclass(frozen=True)
class ConservativeEvidenceStrategy(ResolutionStrategy):
    assignment_threshold: float = 0.85
    review_threshold: float = 0.60
    margin_threshold: float = 0.08
    min_voice_duration_seconds: float = 2.5
    name: str = "review_heavy_low_false_assignment"

    def predict_case(self, case: EvalCase) -> CasePrediction:
        return CasePrediction(
            case_id=case.case_id,
            strategy=self.name,
            segments=[self._predict_segment(segment) for segment in case.segments],
        )

    def _predict_segment(self, segment: SegmentCase) -> SegmentPrediction:
        candidates = sorted(
            segment.evidence_candidates,
            key=lambda item: item.confidence,
            reverse=True,
        )
        if not candidates:
            return _unknown_prediction(segment, self.name, "no_candidate")

        top = candidates[0]
        runner_up = candidates[1].confidence if len(candidates) > 1 else 0.0
        margin = top.confidence - runner_up

        voice_evidence = "voice" in top.evidence_types
        face_evidence = "face" in top.evidence_types
        enough_voice = not voice_evidence or top.duration_seconds >= self.min_voice_duration_seconds
        multimodal = len(set(top.evidence_types) & {"voice", "face", "active_speaker"}) >= 2

        if (
            top.confidence >= self.assignment_threshold
            and margin >= self.margin_threshold
            and enough_voice
            and (face_evidence or multimodal)
        ):
            return _resolved_prediction(segment, self.name, top)

        if top.confidence >= self.assignment_threshold:
            return _review_prediction(
                segment,
                self.name,
                top,
                "candidate_below_safe_assignment_threshold",
            )

        return _unknown_prediction(segment, self.name, "weak_candidate")


def available_strategies() -> dict[str, ResolutionStrategy]:
    return {
        "baseline_unknown": BaselineUnknownStrategy(),
        "risky_top_candidate": RiskyTopCandidateStrategy(),
        "review_heavy_low_false_assignment": ConservativeEvidenceStrategy(),
    }
