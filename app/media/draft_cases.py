from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.workspaces import DEFAULT_WORKSPACE, resolve_workspace


def create_segment_draft_cases(
    workspace: Path,
    *,
    parent_case_path: Path,
    segments_manifest_path: Path,
) -> list[Path]:
    parent_case = json.loads(parent_case_path.read_text(encoding="utf-8"))
    segments_manifest = json.loads(segments_manifest_path.read_text(encoding="utf-8"))

    drafts_root = workspace / "datasets" / "drafts"
    cases_root = drafts_root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)

    created_paths: list[Path] = []
    for segment in segments_manifest.get("segments", []):
        draft_case = _segment_case(parent_case, segment, workspace)
        case_path = cases_root / f"{draft_case['case_id']}.json"
        case_path.write_text(json.dumps(draft_case, indent=2) + "\n", encoding="utf-8")
        created_paths.append(case_path)

    _ensure_manifest_cases(drafts_root / "manifest.json", [path.name for path in created_paths])
    return created_paths


def _segment_case(
    parent_case: dict[str, Any],
    segment: dict[str, Any],
    workspace: Path,
) -> dict[str, Any]:
    segment_id = str(segment["segment_id"])
    source = dict(parent_case.get("source", {}))
    source["parent_case_id"] = parent_case["case_id"]

    segment_media_uri = _workspace_relative_media_uri(str(segment["media_uri"]), workspace)
    clip_start = float(segment["start"])
    clip_end = float(segment["end"])

    return {
        "case_id": segment_id,
        "source": source,
        "media": {
            "media_type": parent_case.get("media_type", "video"),
            "media_uri": segment_media_uri,
            "clip_start": clip_start,
            "clip_end": clip_end,
            "duration": segment.get("duration"),
            "parent_media_uri": parent_case.get("media", {}).get(
                "media_uri",
                parent_case.get("media_uri"),
            ),
            "parent_segments_manifest": parent_case.get("media", {}).get("segments_manifest"),
            "segment_index": segment.get("index"),
        },
        "media_uri": segment_media_uri,
        "known_people_set_id": parent_case.get("known_people_set_id", "seed_podcast"),
        "media_type": parent_case.get("media_type", "video"),
        "conditions": dict(parent_case.get("conditions", {})),
        "speakers": list(parent_case.get("speakers", [])),
        "segments": [],
        "annotation": {
            "status": "draft",
            "reviewed_by": "",
            "review_level": "rough",
            "notes": (
                "Segment draft generated from media chunk. Needs speaker list, "
                "transcript, diarization, and reviewed speaker labels."
            ),
        },
    }


def _workspace_relative_media_uri(media_uri: str, workspace: Path) -> str:
    normalized = media_uri.replace("\\", "/")
    workspace_prefix = workspace.as_posix().rstrip("/") + "/datasets/drafts/"
    if normalized.startswith(workspace_prefix):
        return normalized.removeprefix(workspace_prefix)
    return normalized


def _ensure_manifest_cases(path: Path, case_filenames: list[str]) -> None:
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "name": "drafts",
            "description": "Partially prepared cases that are not yet gold-labelled.",
            "status": "draft",
            "role": "source_drafts",
            "cases": [],
        }
    manifest.setdefault("status", "draft")
    manifest.setdefault("role", "source_drafts")
    cases = manifest.setdefault("cases", [])
    for case_filename in case_filenames:
        if case_filename not in cases:
            cases.append(case_filename)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create draft cases from a segment manifest.")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, type=Path)
    parser.add_argument("--parent-case", required=True, type=Path)
    parser.add_argument("--segments-manifest", required=True, type=Path)
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if workspace is None:
        raise ValueError("workspace is required")
    create_segment_draft_cases(
        workspace,
        parent_case_path=args.parent_case,
        segments_manifest_path=args.segments_manifest,
    )


if __name__ == "__main__":
    main()
