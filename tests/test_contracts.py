from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.bootstrap.contracts import load_bootstrap_contracts, write_bootstrap_readiness_report


def test_load_bootstrap_contracts() -> None:
    contracts = load_bootstrap_contracts()

    assert (
        contracts.domain.domain
        == "multimodal_identity_resolution_for_speaker_attributed_transcription"
    )
    assert "segment_id" in contracts.output.transcript_segment.required_fields
    assert contracts.metrics.primary_metric.name == "false_assignment_rate"
    assert "verification" in contracts.harness_search.change_surfaces
    assert "declare_change_surface" in contracts.harness_search.candidate_requirements


def test_contract_loader_rejects_missing_output_fields(tmp_path: Path) -> None:
    source = Path("bootstrap")
    target = tmp_path / "bootstrap"
    target.mkdir()
    for path in source.glob("*.yaml"):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if path.name == "output_contract.yaml":
            payload["transcript_segment"]["required_fields"] = []
        (target / path.name).write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid bootstrap contract"):
        load_bootstrap_contracts(target)


def test_write_bootstrap_readiness_report(tmp_path: Path) -> None:
    contracts = load_bootstrap_contracts()
    report_path = write_bootstrap_readiness_report(contracts, tmp_path / "readiness.json")

    assert report_path.exists()
    assert "false_assignment_rate" in report_path.read_text(encoding="utf-8")
