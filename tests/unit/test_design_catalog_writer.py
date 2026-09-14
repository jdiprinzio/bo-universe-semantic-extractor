"""Unit tests for design-catalog CSV generation (column order, sorting, determinism)."""

from __future__ import annotations

from bo_semantic_extractor.documentation.design_catalog_writer import (
    generate_join_catalog_csv,
    generate_object_catalog_csv,
)
from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.models.design_catalog import (
    BUSINESS_LAYER_SOURCE_SYSTEM,
    JoinCatalogRecord,
    ObjectCatalogRecord,
)


def test_object_catalog_csv_has_exact_requested_column_order() -> None:
    csv_text = generate_object_catalog_csv([])
    header = csv_text.strip().splitlines()[0]
    assert header == (
        "object_id,object_name,object_type,folder_path,description,"
        "source_system,verification_status"
    )


def test_object_catalog_csv_is_sorted_by_object_id() -> None:
    records = [
        ObjectCatalogRecord(
            object_id="OBJ_2",
            object_name="B",
            object_type="dimension",
            source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        ),
        ObjectCatalogRecord(
            object_id="OBJ_1",
            object_name="A",
            object_type="dimension",
            source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        ),
    ]
    lines = generate_object_catalog_csv(records).strip().splitlines()
    assert lines[1].startswith("OBJ_1,")
    assert lines[2].startswith("OBJ_2,")


def test_join_catalog_csv_sorted_numerically_by_join_id() -> None:
    records = [
        JoinCatalogRecord(
            join_id="10", left_object="L", right_object="R", join_expression="L.K=R.K",
            join_type="UNKNOWN", cardinality="UNKNOWN",
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        ),
        JoinCatalogRecord(
            join_id="2", left_object="L", right_object="R", join_expression="L.K=R.K",
            join_type="UNKNOWN", cardinality="UNKNOWN",
            verification_status=EvidenceVerificationStatus.CONFIRMED,
        ),
    ]
    lines = generate_join_catalog_csv(records).strip().splitlines()
    assert lines[1].startswith("2,")
    assert lines[2].startswith("10,")
