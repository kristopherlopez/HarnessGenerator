from __future__ import annotations

from pathlib import Path

from app.transcription.deepgram import draft_case_from_deepgram_response


def test_deepgram_response_populates_draft_case(tmp_path: Path) -> None:
    case = {
        "case_id": "example_part_000",
        "source": {"source_id": "example"},
        "media_uri": "media/example/segments/example_part_000.mp4",
        "conditions": {"speaker_count": 0, "has_unknown_speakers": True},
        "speakers": [],
        "segments": [],
        "annotation": {"status": "draft", "reviewed_by": "", "review_level": "rough"},
    }
    response = {
        "results": {
            "utterances": [
                {
                    "id": "utt_001",
                    "start": 0.1,
                    "end": 2.4,
                    "transcript": "Hello there.",
                    "speaker": 0,
                    "confidence": 0.93,
                },
                {
                    "id": "utt_002",
                    "start": 2.5,
                    "end": 4.0,
                    "transcript": "Good to be here.",
                    "speaker": 1,
                    "confidence": 0.88,
                },
            ]
        }
    }

    updated = draft_case_from_deepgram_response(
        case=case,
        response=response,
        provider_output_path=tmp_path / "provider.json",
        workspace=tmp_path,
    )

    assert updated["conditions"]["speaker_count"] == 2
    assert [speaker["display_name"] for speaker in updated["speakers"]] == [
        "Speaker 0",
        "Speaker 1",
    ]
    assert [segment["true_display_name"] for segment in updated["segments"]] == [
        "Speaker 0",
        "Speaker 1",
    ]
    assert [speaker["person_id"] for speaker in updated["speakers"]] == [1, 2]
    assert [segment["true_person_id"] for segment in updated["segments"]] == [1, 2]
    assert [segment["segment_id"] for segment in updated["segments"]] == [1, 2]
    assert updated["segments"][0]["confidence"] == 0.93
    assert updated["segments"][0]["speaker_type"] == "unknown"
    assert updated["annotation"]["provider"] == "deepgram_diarized_transcription"
