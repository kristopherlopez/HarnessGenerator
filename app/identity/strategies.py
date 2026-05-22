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
        person_id=0,
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
        person_id=0,
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


def _review_budget_exceeded_prediction(prediction: SegmentPrediction) -> SegmentPrediction:
    return SegmentPrediction(
        segment_id=prediction.segment_id,
        start=prediction.start,
        end=prediction.end,
        text=prediction.text,
        speaker_id=prediction.speaker_id,
        person_id=0,
        display_name="Unknown Speaker",
        confidence=0.0,
        resolution_status="unknown",
        evidence_summary=EvidenceSummary(
            evidence_types=prediction.evidence_summary.evidence_types,
            strongest_signal=prediction.evidence_summary.strongest_signal,
            provenance=prediction.evidence_summary.provenance,
            conflicts=[*prediction.evidence_summary.conflicts, "review_budget_exceeded"],
        ),
        review=ReviewState(required=False, reason="review_budget_exceeded"),
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
    voice_only_assignment_threshold: float = 0.80
    review_threshold: float = 0.60
    max_review_rate: float = 0.25
    minimum_review_slots: int = 1
    overlap_handling_policy: str = "require_corroborating_signal_on_high_overlap"
    margin_threshold: float = 0.08
    voice_only_margin_threshold: float = 0.10
    min_voice_duration_seconds: float = 2.5
    min_voice_only_duration_seconds: float = 5.0
    high_overlap_levels: tuple[str, ...] = ("high",)
    name: str = "review_heavy_low_false_assignment"

    def predict_case(self, case: EvalCase) -> CasePrediction:
        predictions = [
            self._predict_segment(segment, case.conditions)
            for segment in case.segments
        ]
        return CasePrediction(
            case_id=case.case_id,
            strategy=self.name,
            segments=self._apply_review_budget(predictions),
        )

    def _predict_segment(
        self,
        segment: SegmentCase,
        conditions: dict[str, object],
    ) -> SegmentPrediction:
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
        voice_only = set(top.evidence_types) == {"voice"}
        high_overlap = self._is_high_overlap(conditions)

        if (
            top.confidence >= self.assignment_threshold
            and margin >= self.margin_threshold
            and enough_voice
            and (face_evidence or multimodal)
        ):
            return _resolved_prediction(segment, self.name, top)

        if (
            voice_only
            and not high_overlap
            and top.confidence >= self.voice_only_assignment_threshold
            and margin >= self.voice_only_margin_threshold
            and top.duration_seconds >= self.min_voice_only_duration_seconds
            and top.provenance
        ):
            return _resolved_prediction(segment, self.name, top)

        if self._has_ambiguous_voice_conflict(candidates, top, margin):
            return _review_prediction(
                segment,
                self.name,
                top,
                "ambiguous_voice_candidate_margin",
            )

        if top.confidence >= self.assignment_threshold:
            return _review_prediction(
                segment,
                self.name,
                top,
                "candidate_below_safe_assignment_threshold",
            )

        return _unknown_prediction(segment, self.name, "weak_candidate")

    def _has_ambiguous_voice_conflict(
        self,
        candidates: list[EvidenceCandidate],
        top: EvidenceCandidate,
        margin: float,
    ) -> bool:
        if len(candidates) < 2:
            return False
        if set(top.evidence_types) != {"voice"}:
            return False
        runner_up = candidates[1]
        return (
            set(runner_up.evidence_types) == {"voice"}
            and top.confidence >= self.voice_only_assignment_threshold
            and margin < self.voice_only_margin_threshold
            and top.duration_seconds >= self.min_voice_only_duration_seconds
            and bool(top.provenance)
            and bool(runner_up.provenance)
        )

    def _is_high_overlap(self, conditions: dict[str, object]) -> bool:
        if self.overlap_handling_policy != "require_corroborating_signal_on_high_overlap":
            return False
        overlap_level = str(conditions.get("overlap_level", "")).lower()
        return overlap_level in self.high_overlap_levels

    def _apply_review_budget(
        self,
        predictions: list[SegmentPrediction],
    ) -> list[SegmentPrediction]:
        review_indexes = [
            index
            for index, prediction in enumerate(predictions)
            if prediction.resolution_status == "needs_review"
        ]
        review_budget = self._review_budget(len(predictions))
        if len(review_indexes) <= review_budget:
            return predictions

        selected_review_indexes = set(
            sorted(
                review_indexes,
                key=lambda index: self._review_priority(predictions[index]),
                reverse=True,
            )[:review_budget]
        )
        return [
            prediction
            if prediction.resolution_status != "needs_review" or index in selected_review_indexes
            else _review_budget_exceeded_prediction(prediction)
            for index, prediction in enumerate(predictions)
        ]

    def _review_budget(self, segment_count: int) -> int:
        if segment_count == 0:
            return 0
        budget = int(segment_count * self.max_review_rate)
        if self.minimum_review_slots > 0:
            budget = max(self.minimum_review_slots, budget)
        return min(segment_count, budget)

    def _review_priority(self, prediction: SegmentPrediction) -> tuple[float, float]:
        duration = prediction.end - prediction.start
        return (prediction.confidence, duration)


def available_strategies() -> dict[str, ResolutionStrategy]:
    return {
        "baseline_unknown": BaselineUnknownStrategy(),
        "risky_top_candidate": RiskyTopCandidateStrategy(),
        "review_heavy_low_false_assignment": ConservativeEvidenceStrategy(),
    }
