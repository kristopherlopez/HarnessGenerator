from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

ResolutionStatus = Literal["resolved", "unknown", "needs_review"]
type SegmentId = int | str
type PersonId = int


class EvidenceCandidate(BaseModel):
    person_id: PersonId
    display_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_types: list[str]
    duration_seconds: float = Field(ge=0.0)
    provenance: list[str] = Field(default_factory=list)


class SegmentCase(BaseModel):
    segment_id: SegmentId
    start: float
    end: float
    text: str
    true_person_id: PersonId
    true_display_name: str
    speaker_type: Literal["known", "unknown"]
    evidence_candidates: list[EvidenceCandidate] = Field(default_factory=list)


class EvalCase(BaseModel):
    case_id: str
    media_uri: str
    source: dict[str, object] | None = None
    media: dict[str, object] | None = None
    known_people_set_id: str
    media_type: Literal["audio", "video", "caption_file"]
    conditions: dict[str, object]
    speakers: list[dict[str, object]] = Field(default_factory=list)
    segments: list[SegmentCase]
    annotation: dict[str, object] | None = None

    @model_validator(mode="before")
    @classmethod
    def derive_legacy_media_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        media = data.get("media")
        if isinstance(media, dict):
            data.setdefault("media_uri", media.get("media_uri"))
            data.setdefault("media_type", media.get("media_type"))
        return data


class EvidenceSummary(BaseModel):
    evidence_types: list[str]
    strongest_signal: str
    provenance: list[str]
    conflicts: list[str] = Field(default_factory=list)


class ReviewState(BaseModel):
    required: bool
    reason: str
    human_reviewed: bool = False


class SegmentPrediction(BaseModel):
    segment_id: SegmentId
    start: float
    end: float
    text: str
    speaker_id: str
    person_id: PersonId
    display_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    resolution_status: ResolutionStatus
    evidence_summary: EvidenceSummary
    review: ReviewState


class CasePrediction(BaseModel):
    case_id: str
    strategy: str
    segments: list[SegmentPrediction]
