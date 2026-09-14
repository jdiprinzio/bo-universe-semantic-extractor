"""Unit tests for the Query Panel outline parser: raw models + recursive traversal + normalization."""

from __future__ import annotations

import json
from pathlib import Path

from bo_semantic_extractor.models import RawArtifact
from bo_semantic_extractor.models.query_panel_outline_normalized import (
    OutlineClassificationStatus,
)
from bo_semantic_extractor.models.query_panel_outline_raw import (
    QueryPanelOutlineNode,
    QueryPanelOutlineUserData,
)
from bo_semantic_extractor.normalization.query_panel_outline import (
    classify_source_node_id,
    extract_lineage_candidates,
    iter_outline_nodes,
    normalize_outline_artifact,
    parse_query_panel_outline_artifact,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bo_rest"


def _load_artifact() -> RawArtifact:
    path = FIXTURES_DIR / "query_panel_outline.real_shape.sample.json"
    return RawArtifact.model_validate_json(path.read_text(encoding="utf-8"))


def _make_node(
    name: str,
    node_id: str,
    *,
    child: bool = False,
    obj_type: int = 0,
    help_text: str | None = None,
    related_id: str | None = None,
    description: str | None = None,
    nodes: list[QueryPanelOutlineNode] | None = None,
) -> QueryPanelOutlineNode:
    return QueryPanelOutlineNode(
        name=name,
        child=child,
        objType=obj_type,
        help=help_text,
        userData=QueryPanelOutlineUserData(b=node_id, c=2, g=related_id, i=description),
        nodes=nodes or [],
    )


# ---------------------------------------------------------------------------
# Recursive traversal
# ---------------------------------------------------------------------------


def test_recursive_traversal_visits_every_node_in_the_fixture() -> None:
    artifact = _load_artifact()
    root = parse_query_panel_outline_artifact(artifact)
    visited = list(iter_outline_nodes(root))
    assert len(visited) == 5
    assert {node.name for node, _, _ in visited} == {
        "Profit Center Dimension",
        "Above Profit Center Hierarchy",
        "Organization",
        "Division",
        "Division Desc",
    }


def test_normalize_outline_artifact_produces_one_record_per_node() -> None:
    artifact = _load_artifact()
    records = normalize_outline_artifact(artifact)
    assert len(records) == 5
    assert {r.source_node_id for r in records} == {
        "CLS_100",
        "CLS_101",
        "OBJ_1001",
        "OBJ_1002",
        "OBJ_1003",
    }


# ---------------------------------------------------------------------------
# Nested paths
# ---------------------------------------------------------------------------


def test_nested_paths_are_computed_via_traversal_not_guessed() -> None:
    artifact = _load_artifact()
    records = {r.source_node_id: r for r in normalize_outline_artifact(artifact)}

    root = records["CLS_100"]
    assert root.full_object_path == "Profit Center Dimension"
    assert root.parent_object_path is None

    folder = records["CLS_101"]
    assert folder.full_object_path == "Profit Center Dimension/Above Profit Center Hierarchy"
    assert folder.parent_object_path == "Profit Center Dimension"

    organization = records["OBJ_1001"]
    assert organization.full_object_path == (
        "Profit Center Dimension/Above Profit Center Hierarchy/Organization"
    )
    assert organization.parent_object_path == "Profit Center Dimension/Above Profit Center Hierarchy"

    division_desc = records["OBJ_1003"]
    assert division_desc.full_object_path == (
        "Profit Center Dimension/Above Profit Center Hierarchy/Division/Division Desc"
    )
    assert division_desc.parent_object_path == (
        "Profit Center Dimension/Above Profit Center Hierarchy/Division"
    )


# ---------------------------------------------------------------------------
# Duplicate names
# ---------------------------------------------------------------------------


def test_duplicate_names_under_different_parents_get_distinct_paths() -> None:
    left_leaf = _make_node("Amount", "OBJ_2001")
    right_leaf = _make_node("Amount", "OBJ_2002")
    root = _make_node(
        "Root",
        "CLS_200",
        child=True,
        nodes=[
            _make_node("Left", "CLS_201", child=True, nodes=[left_leaf]),
            _make_node("Right", "CLS_202", child=True, nodes=[right_leaf]),
        ],
    )

    visited = {node.userData.b: full_path for node, full_path, _ in iter_outline_nodes(root)}

    assert visited["OBJ_2001"] == "Root/Left/Amount"
    assert visited["OBJ_2002"] == "Root/Right/Amount"
    assert visited["OBJ_2001"] != visited["OBJ_2002"]


def test_duplicate_names_produce_separate_normalized_records_not_merged() -> None:
    artifact = RawArtifact(
        run_id="run-test-0001",
        source_system="BO_QUERY_PANEL_INTERNAL",
        source_operation="queryPanelOutline",
        source_identifier="TEST_UNIVERSE",
        retrieved_at_utc="2026-01-01T00:00:00Z",
        content_hash_sha256="0" * 64,
        payload=_make_node(
            "Root",
            "CLS_200",
            child=True,
            nodes=[
                _make_node("Left", "CLS_201", child=True, nodes=[_make_node("Amount", "OBJ_2001")]),
                _make_node("Right", "CLS_202", child=True, nodes=[_make_node("Amount", "OBJ_2002")]),
            ],
        ).model_dump(),
    )
    records = normalize_outline_artifact(artifact)
    amounts = [r for r in records if r.object_name == "Amount"]
    assert len(amounts) == 2
    assert {r.full_object_path for r in amounts} == {"Root/Left/Amount", "Root/Right/Amount"}


# ---------------------------------------------------------------------------
# Lineage extraction
# ---------------------------------------------------------------------------


def test_lineage_extraction_detects_table_column_pattern_in_help_and_userdata_i() -> None:
    assert extract_lineage_candidates("SAMPLE_DIMENSION.ORG_NAME", None) == [
        "SAMPLE_DIMENSION.ORG_NAME"
    ]
    assert extract_lineage_candidates(None, "Organization : SAMPLE_DIMENSION.ORG_NAME") == [
        "SAMPLE_DIMENSION.ORG_NAME"
    ]


def test_lineage_extraction_deduplicates_across_both_fields() -> None:
    candidates = extract_lineage_candidates(
        "SAMPLE_DIMENSION.ORG_NAME", "Organization : SAMPLE_DIMENSION.ORG_NAME"
    )
    assert candidates == ["SAMPLE_DIMENSION.ORG_NAME"]


def test_lineage_extraction_returns_empty_for_plain_text() -> None:
    assert extract_lineage_candidates("Sample division object", "Sample division object") == []


def test_fixture_lineage_candidates_only_present_on_organization_node() -> None:
    artifact = _load_artifact()
    records = {r.source_node_id: r for r in normalize_outline_artifact(artifact)}
    assert records["OBJ_1001"].lineage_candidates == ["SAMPLE_DIMENSION.ORG_NAME"]
    assert records["OBJ_1002"].lineage_candidates == []
    assert records["OBJ_1003"].lineage_candidates == []
    assert records["CLS_100"].lineage_candidates == []


# ---------------------------------------------------------------------------
# Node preservation (raw fields, including unknown/future fields)
# ---------------------------------------------------------------------------


def test_raw_node_preserves_every_known_field_exactly() -> None:
    artifact = _load_artifact()
    root = parse_query_panel_outline_artifact(artifact)
    assert root.name == "Profit Center Dimension"
    assert root.child is True
    assert root.objType == 0
    assert root.userData.b == "CLS_100"
    assert root.userData.c == 20
    assert root.userData.h == ""
    assert root.userData.j == 0


def test_raw_node_preserves_unknown_future_fields_via_extra_allow() -> None:
    raw_payload = json.loads((FIXTURES_DIR / "query_panel_outline.real_shape.sample.json").read_text())
    raw_payload["payload"]["futureNodeField"] = "unmapped-value"
    raw_payload["payload"]["userData"]["z"] = "unmapped-userdata-value"

    node = QueryPanelOutlineNode.model_validate(raw_payload["payload"])

    assert node.model_extra is not None
    assert node.model_extra["futureNodeField"] == "unmapped-value"
    assert node.userData.model_extra is not None
    assert node.userData.model_extra["z"] == "unmapped-userdata-value"
    # Round-tripping through dump must not silently drop the unmapped field.
    assert node.model_dump()["futureNodeField"] == "unmapped-value"


# ---------------------------------------------------------------------------
# Leaf nodes
# ---------------------------------------------------------------------------


def test_leaf_nodes_have_no_children_and_confirmed_object_classification() -> None:
    artifact = _load_artifact()
    records = normalize_outline_artifact(artifact)
    leaf_ids = {"OBJ_1001", "OBJ_1002", "OBJ_1003"}

    for node, _, _ in iter_outline_nodes(parse_query_panel_outline_artifact(artifact)):
        if node.userData.b in leaf_ids and node.userData.b != "OBJ_1002":
            # OBJ_1002 ("Division") has a nested child in this fixture; only true leaves checked here.
            assert node.child is False
            assert node.nodes == []

    for record in records:
        if record.source_node_id in {"OBJ_1001", "OBJ_1003"}:
            assert record.classification_status is OutlineClassificationStatus.CONFIRMED_OBJECT


def test_classify_source_node_id_object_prefix() -> None:
    assert classify_source_node_id("OBJ_9999") is OutlineClassificationStatus.CONFIRMED_OBJECT


def test_classify_source_node_id_unknown_prefix_is_never_guessed() -> None:
    assert (
        classify_source_node_id("XYZ_1")
        is OutlineClassificationStatus.UNKNOWN_IDENTIFIER_PATTERN
    )


# ---------------------------------------------------------------------------
# Child (folder/class) nodes
# ---------------------------------------------------------------------------


def test_child_nodes_have_nested_children_and_confirmed_class_classification() -> None:
    artifact = _load_artifact()
    root = parse_query_panel_outline_artifact(artifact)
    assert root.child is True
    assert len(root.nodes) == 1

    records = {r.source_node_id: r for r in normalize_outline_artifact(artifact)}
    assert records["CLS_100"].classification_status is OutlineClassificationStatus.CONFIRMED_CLASS
    assert records["CLS_101"].classification_status is OutlineClassificationStatus.CONFIRMED_CLASS


def test_classify_source_node_id_class_prefix() -> None:
    assert classify_source_node_id("CLS_1") is OutlineClassificationStatus.CONFIRMED_CLASS


def test_division_node_has_child_true_and_one_nested_object() -> None:
    """"Division" (OBJ_1002) is unusual: `child=True` despite an OBJ_ id, with one nested leaf."""
    artifact = _load_artifact()
    root = parse_query_panel_outline_artifact(artifact)
    division = root.nodes[0].nodes[1]
    assert division.name == "Division"
    assert division.child is True
    assert len(division.nodes) == 1
    assert division.nodes[0].name == "Division Desc"
