"""Unit tests for typed models, including the ObjectType(unknown) preservation rule."""

from __future__ import annotations

from datetime import UTC, datetime

from bo_semantic_extractor.models import ObjectType, UniverseObject


def test_unmapped_object_type_is_preserved_as_unknown() -> None:
    """An object type not in the allowed list must map to UNKNOWN, never a guessed type."""
    obj = UniverseObject(
        universe_cuid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        object_id="OBJ_0003",
        technical_name="LEGACY_FLAG",
        object_name="Legacy Flag",
        folder_path="Misc",
        object_type=ObjectType.UNKNOWN,
        extraction_source="BO_SEMANTIC_LAYER_REST",
        source_evidence_path="raw/run-sample-0001/objects/OBJ_0003.json",
    )
    assert obj.object_type is ObjectType.UNKNOWN


def test_measure_round_trips_through_model_dump() -> None:
    obj = UniverseObject(
        universe_cuid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        object_id="OBJ_0002",
        technical_name="SALES_AMT",
        object_name="Sales Amount",
        folder_path="Sales",
        object_type=ObjectType.MEASURE,
        aggregation_function="sum",
        extraction_source="BO_SEMANTIC_LAYER_REST",
        source_evidence_path="raw/run-sample-0001/objects/OBJ_0002.json",
    )
    dumped = obj.model_dump()
    assert dumped["aggregation_function"] == "sum"
    assert dumped["object_type"] == ObjectType.MEASURE


def test_semantic_enrichment_defaults_to_ai_proposed() -> None:
    from bo_semantic_extractor.models import ReviewStatus, SemanticEnrichment

    enrichment = SemanticEnrichment(
        canonical_term="Sales Amount",
        generated_by_model="test-model",
        generated_at_utc=datetime.now(UTC),
    )
    assert enrichment.review_status == ReviewStatus.AI_PROPOSED
