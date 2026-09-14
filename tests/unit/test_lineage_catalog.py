"""Unit tests for lineage-candidate extraction and catalog building."""

from __future__ import annotations

from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.models.design_catalog import (
    BUSINESS_LAYER_SOURCE_SYSTEM,
    DATA_FOUNDATION_SOURCE_SYSTEM,
    ExpressionCatalogRecord,
    TableCatalogRecord,
)
from bo_semantic_extractor.normalization.lineage_catalog import (
    build_lineage_catalog,
    extract_table_column_candidates,
)


def test_extract_table_column_candidates_finds_plain_references() -> None:
    candidates = extract_table_column_candidates("SUM(SAMPLE_FACT.SAMPLE_AMT)")
    assert candidates == [("SAMPLE_FACT", "SAMPLE_AMT")]


def test_extract_table_column_candidates_ignores_business_object_cross_references() -> None:
    """`@Select(Folder\\Object)` references use backslashes, never a literal dot, so they must
    not be mistaken for a table.column reference."""
    candidates = extract_table_column_candidates(
        "Case When @Select(Date Dimension\\Year) = 1 Then SAMPLE_FACT.AMT Else 0 End"
    )
    assert candidates == [("SAMPLE_FACT", "AMT")]


def test_extract_table_column_candidates_dedupes_and_preserves_order() -> None:
    candidates = extract_table_column_candidates("SAMPLE_FACT.AMT + SAMPLE_FACT.AMT + SAMPLE_FACT.QTY")
    assert candidates == [("SAMPLE_FACT", "AMT"), ("SAMPLE_FACT", "QTY")]


def test_build_lineage_catalog_marks_known_table_as_parsed_unverified() -> None:
    expressions = [
        ExpressionCatalogRecord(
            object_id="OBJ_1",
            object_name="Sample Measure",
            select_expression="SUM(SAMPLE_FACT.AMT)",
            source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        )
    ]
    tables = [
        TableCatalogRecord(
            table_name="SAMPLE_FACT",
            table_type="UNKNOWN",
            source_system=DATA_FOUNDATION_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        )
    ]
    lineage = build_lineage_catalog(expressions, tables)
    assert len(lineage) == 1
    assert lineage[0].verification_status is EvidenceVerificationStatus.PARSED_UNVERIFIED
    assert lineage[0].physical_hana_object == "UNKNOWN"
    assert lineage[0].physical_hana_column == "UNKNOWN"


def test_build_lineage_catalog_marks_unknown_table_as_unknown() -> None:
    expressions = [
        ExpressionCatalogRecord(
            object_id="OBJ_2",
            object_name="Other Measure",
            select_expression="SUM(NOT_IN_TABLE_CATALOG.AMT)",
            source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        )
    ]
    lineage = build_lineage_catalog(expressions, tables=[])
    assert lineage[0].verification_status is EvidenceVerificationStatus.UNKNOWN


def test_build_lineage_catalog_skips_expressions_without_candidates() -> None:
    expressions = [
        ExpressionCatalogRecord(
            object_id="OBJ_3",
            object_name="No Candidate",
            select_expression="1",
            source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        )
    ]
    assert build_lineage_catalog(expressions, tables=[]) == []
