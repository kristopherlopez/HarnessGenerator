from __future__ import annotations

import json
from pathlib import Path

from app.intake.youtube_seed import seed_youtube_source, source_id_from_url, video_id_from_url


def test_video_id_from_url() -> None:
    assert video_id_from_url("https://www.youtube.com/watch?v=gG1Lq2pIgGM") == "gG1Lq2pIgGM"
    assert video_id_from_url("https://youtu.be/gG1Lq2pIgGM") == "gG1Lq2pIgGM"
    assert source_id_from_url("https://www.youtube.com/watch?v=gG1Lq2pIgGM") == (
        "youtube_gG1Lq2pIgGM"
    )


def test_seed_youtube_source_creates_intake_and_draft(tmp_path: Path) -> None:
    draft_path = seed_youtube_source(
        tmp_path,
        "https://www.youtube.com/watch?v=gG1Lq2pIgGM",
        title="Example Title",
        channel="Example Channel",
        expected_speakers=["Alice Example", "Bob Example"],
        clip_start=10.0,
        clip_end=70.0,
        fetch_metadata=False,
    )

    intake = tmp_path / "intake" / "youtube_links.jsonl"
    manifest = tmp_path / "datasets" / "drafts" / "manifest.json"

    assert draft_path.exists()
    assert intake.exists()
    assert manifest.exists()

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["source"]["title"] == "Example Title"
    assert draft["media"]["clip_start"] == 10.0
    assert draft["media"]["clip_end"] == 70.0
    assert [speaker["display_name"] for speaker in draft["speakers"]] == [
        "Alice Example",
        "Bob Example",
    ]
    assert "youtube_gG1Lq2pIgGM.json" in json.loads(
        manifest.read_text(encoding="utf-8")
    )["cases"]

