from __future__ import annotations

import json
from pathlib import Path

from app.media.draft_cases import create_segment_draft_cases


def test_create_segment_draft_cases(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    parent_case_path = workspace / "datasets" / "drafts" / "cases" / "parent.json"
    manifest_path = (
        workspace / "datasets" / "drafts" / "media" / "parent" / "segments_manifest.json"
    )
    parent_case_path.parent.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True)

    parent_case_path.write_text(
        json.dumps(
            {
                "case_id": "parent",
                "source": {"input_type": "youtube_url", "youtube_url": "https://example.test"},
                "media": {"media_uri": "media/parent/source.mp4"},
                "media_uri": "media/parent/source.mp4",
                "known_people_set_id": "seed",
                "media_type": "video",
                "conditions": {"speaker_count": 0},
                "speakers": [],
                "segments": [],
            }
        ),
        encoding="utf-8",
    )
    segment_media = (
        workspace / "datasets" / "drafts" / "media" / "parent" / "segments" / "part_000.mp4"
    )
    manifest_path.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "index": 0,
                        "segment_id": "parent_part_000",
                        "media_uri": segment_media.as_posix(),
                        "start": 0.0,
                        "end": 300.0,
                        "duration": 300.0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    created = create_segment_draft_cases(
        workspace,
        parent_case_path=parent_case_path,
        segments_manifest_path=manifest_path,
    )

    assert len(created) == 1
    draft_case = json.loads(created[0].read_text(encoding="utf-8"))
    assert draft_case["case_id"] == "parent_part_000"
    assert draft_case["media"]["media_uri"] == "media/parent/segments/part_000.mp4"
    assert draft_case["segments"] == []
