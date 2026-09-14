"""Unit tests for validation rules (VALIDATE stage)."""

from __future__ import annotations

from pathlib import Path

from bo_semantic_extractor.models import ObjectType, UniverseObject
from bo_semantic_extractor.validation.findings import FindingCategory
from bo_semantic_extractor.validation.rules import (
    find_duplicate_object_names,
    find_missing_descriptions,
    find_unknown_object_types,
    run_all_validations,
    validate_raw_evidence_linkage,
)

UNIVERSE_CUID = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def _make_object(**overrides: object) -> UniverseObject:
    defaults: dict[str, object] = {
        "universe_cuid": UNIVERSE_CUID,
        "object_id": "OBJ_0001",
        "technical_name": "CUST_ID",
        "object_name": "Customer ID",
        "folder_path": "Customer",
        "object_type": ObjectType.DIMENSION,
        "extraction_source": "BO_SEMANTIC_LAYER_REST",
        "source_evidence_path": "tests/fixtures/bo_rest/universe_detail.sample.json",
    }
    defaults.update(overrides)
    return UniverseObject(**defaults)  # type: ignore[arg-type]


def test_find_duplicate_object_names_flags_all_members_of_the_group() -> None:
    objects = [
        _make_object(object_id="OBJ_0001", object_name="Customer ID", folder_path="Customer"),
        _make_object(object_id="OBJ_0002", object_name="Customer ID", folder_path="Legacy"),
    ]
    findings = find_duplicate_object_names(objects)
    assert len(findings) == 2
    assert all(f.category is FindingCategory.DUPLICATE_OBJECT_NAME for f in findings)


def test_find_duplicate_object_names_ignores_unique_names() -> None:
    objects = [_make_object(object_id="OBJ_0001"), _make_object(object_id="OBJ_0002", object_name="Other")]
    assert find_duplicate_object_names(objects) == []


def test_find_missing_descriptions_flags_only_missing() -> None:
    objects = [
        _make_object(object_id="OBJ_0001", description="has one"),
        _make_object(object_id="OBJ_0002", description=None),
    ]
    findings = find_missing_descriptions(objects)
    assert [f.object_id for f in findings] == ["OBJ_0002"]


def test_find_unknown_object_types_flags_unknown_only() -> None:
    objects = [
        _make_object(object_id="OBJ_0001", object_type=ObjectType.MEASURE),
        _make_object(object_id="OBJ_0002", object_type=ObjectType.UNKNOWN),
    ]
    findings = find_unknown_object_types(objects)
    assert [f.object_id for f in findings] == ["OBJ_0002"]


def test_validate_raw_evidence_linkage_flags_missing_files() -> None:
    objects = [_make_object(object_id="OBJ_0001", source_evidence_path="does/not/exist.json")]
    findings = validate_raw_evidence_linkage(objects, Path.cwd())
    assert len(findings) == 1
    assert findings[0].category is FindingCategory.MISSING_RAW_EVIDENCE


def test_run_all_validations_aggregates_every_rule() -> None:
    objects = [
        _make_object(
            object_id="OBJ_0001",
            description=None,
            object_type=ObjectType.UNKNOWN,
            source_evidence_path="missing.json",
        ),
    ]
    findings = run_all_validations(objects, Path.cwd())
    categories = {f.category for f in findings}
    assert FindingCategory.MISSING_DESCRIPTION in categories
    assert FindingCategory.UNKNOWN_OBJECT_TYPE in categories
    assert FindingCategory.MISSING_RAW_EVIDENCE in categories
