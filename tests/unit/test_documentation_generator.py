"""Unit tests for documentation-generation scaffolding."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bo_semantic_extractor.documentation.generator import (
    generate_extraction_report_markdown,
    generate_object_catalog_csv,
    generate_object_catalog_json_from_outline_records,
    generate_universe_manifest_yaml,
    generate_universe_summary_markdown,
    generate_validation_findings_csv,
    generate_webi_report_inventory_csv,
    write_universe_documentation,
)
from bo_semantic_extractor.models import ObjectType, Universe, UniverseObject
from bo_semantic_extractor.models.query_panel_outline_normalized import (
    OutlineClassificationStatus,
    QueryPanelOutlineRecord,
)
from bo_semantic_extractor.pipeline import StageManifest, StageName, StageStatus
from bo_semantic_extractor.validation.findings import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)

UNIVERSE = Universe(
    universe_cuid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    universe_name="SAMPLE_SALES_UNIVERSE",
    universe_type="UNX",
    repository_path="/Sample/Sales/SAMPLE_SALES_UNIVERSE",
    source_system="BO_SEMANTIC_LAYER_REST",
    extracted_at_utc=datetime(2026, 1, 15, 9, 30, tzinfo=UTC),
)

OBJECTS = [
    UniverseObject(
        universe_cuid=UNIVERSE.universe_cuid,
        object_id="OBJ_0002",
        technical_name="SALES_AMT",
        object_name="Sales Amount",
        folder_path="Sales",
        object_type=ObjectType.MEASURE,
        description="Total sales amount.",
        aggregation_function="sum",
        extraction_source="BO_SEMANTIC_LAYER_REST",
        source_evidence_path="raw/run-sample-0001/objects/OBJ_0002.json",
    ),
    UniverseObject(
        universe_cuid=UNIVERSE.universe_cuid,
        object_id="OBJ_0001",
        technical_name="CUST_ID",
        object_name="Customer ID",
        folder_path="Customer",
        object_type=ObjectType.DIMENSION,
        description=None,
        extraction_source="BO_SEMANTIC_LAYER_REST",
        source_evidence_path="raw/run-sample-0001/objects/OBJ_0001.json",
    ),
]


def test_object_catalog_csv_is_sorted_and_deterministic() -> None:
    csv_text = generate_object_catalog_csv(OBJECTS)
    lines = csv_text.strip().splitlines()
    assert lines[1].startswith("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,OBJ_0001")
    assert lines[2].startswith("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,OBJ_0002")


def test_universe_summary_reports_missing_descriptions() -> None:
    summary = generate_universe_summary_markdown(
        UNIVERSE, OBJECTS, generated_at_utc=datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    )
    assert "Objects missing a description: 1" in summary
    assert "dimension: 1" in summary
    assert "measure: 1" in summary


def test_write_universe_documentation_creates_expected_files(tmp_path: Path) -> None:
    written = write_universe_documentation(UNIVERSE, OBJECTS, tmp_path)
    assert set(written) == {"universe_summary.md", "object_catalog.csv", "object_catalog.json"}
    for path in written.values():
        assert path.exists()


def test_unimplemented_generator_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        generate_webi_report_inventory_csv()


FINDINGS = [
    ValidationFinding(
        finding_id="NODESC-OBJ_0001",
        category=FindingCategory.MISSING_DESCRIPTION,
        severity=FindingSeverity.INFO,
        message="Object 'Customer ID' (OBJ_0001) has no description.",
        universe_cuid=UNIVERSE.universe_cuid,
        object_id="OBJ_0001",
    )
]

STAGE_MANIFESTS = [
    StageManifest(
        stage=StageName.NORMALIZE,
        run_id="run-sample-0001",
        started_at_utc=datetime(2026, 1, 15, 9, 30, tzinfo=UTC),
        completed_at_utc=datetime(2026, 1, 15, 9, 31, tzinfo=UTC),
        status=StageStatus.SUCCESS,
    )
]


def test_generate_validation_findings_csv_is_sorted_and_complete() -> None:
    csv_text = generate_validation_findings_csv(FINDINGS)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "finding_id,category,severity,message,universe_cuid,object_id"
    assert lines[1].startswith("NODESC-OBJ_0001,MISSING_DESCRIPTION")


def test_generate_universe_manifest_yaml_includes_stage_results() -> None:
    manifest_yaml = generate_universe_manifest_yaml(UNIVERSE, "run-sample-0001", STAGE_MANIFESTS)
    assert "run_id: run-sample-0001" in manifest_yaml
    assert "stage: NORMALIZE" in manifest_yaml
    assert "status: SUCCESS" in manifest_yaml


def test_generate_object_catalog_json_from_outline_records_is_sorted_by_path() -> None:
    records = [
        QueryPanelOutlineRecord(
            source_node_id="OBJ_1001",
            object_name="Organization",
            full_object_path="Profit Center Dimension/Organization",
            raw_obj_type=0,
            classification_status=OutlineClassificationStatus.CONFIRMED_OBJECT,
            source_evidence_path="raw/run-1/objects/PER_SAMPLE_100.json",
        ),
        QueryPanelOutlineRecord(
            source_node_id="CLS_100",
            object_name="Profit Center Dimension",
            full_object_path="Profit Center Dimension",
            raw_obj_type=0,
            classification_status=OutlineClassificationStatus.CONFIRMED_CLASS,
            source_evidence_path="raw/run-1/objects/PER_SAMPLE_100.json",
        ),
    ]
    catalog_json = generate_object_catalog_json_from_outline_records(records)
    parsed = json.loads(catalog_json)
    assert [entry["full_object_path"] for entry in parsed] == [
        "Profit Center Dimension",
        "Profit Center Dimension/Organization",
    ]



def test_generate_extraction_report_markdown_summarizes_findings_and_stages() -> None:
    report = generate_extraction_report_markdown(UNIVERSE, OBJECTS, FINDINGS, STAGE_MANIFESTS)
    assert "NORMALIZE: SUCCESS" in report
    assert "Object Count: 2" in report
    assert "MISSING_DESCRIPTION: 1" in report
