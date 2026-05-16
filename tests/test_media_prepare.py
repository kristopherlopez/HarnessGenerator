from __future__ import annotations

import json
from pathlib import Path

from app.media.prepare import write_segment_manifest


def test_write_segment_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_text("not real media", encoding="utf-8")
    segments = [tmp_path / "part_000.mp4", tmp_path / "part_001.mp4"]
    for segment in segments:
        segment.write_text("not real media", encoding="utf-8")

    manifest_path = write_segment_manifest(
        source_id="youtube_example",
        youtube_url="https://www.youtube.com/watch?v=example",
        source_path=source,
        segment_paths=segments,
        segment_seconds=300,
        output_path=tmp_path / "segments_manifest.json",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["segment_seconds"] == 300
    assert manifest["segments"][0]["segment_id"] == "youtube_example_part_000"
    assert manifest["segments"][1]["start"] == 300

