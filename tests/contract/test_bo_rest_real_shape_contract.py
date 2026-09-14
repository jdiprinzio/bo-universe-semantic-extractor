"""Contract tests for the real-shape evidence fixtures under `tests/fixtures/bo_rest/`.

These fixtures were derived from sanitized evidence captured from BusinessObjects' internal
Query Panel service (`docs/evidence/`), **not** the officially documented `/biprws/` REST API —
see `docs/businessobjects_api_requirements.md`. No endpoint has been implemented from this
evidence; these tests only prove the fixtures are well-formed and that their real field shapes
can, in principle, be mapped onto the current typed models (`bo_semantic_extractor.models`).
The mapping logic here is test-local and demonstrative — it is not the production NORMALIZE
converter, which still targets the placeholder contract until a real endpoint is confirmed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bo_semantic_extractor.extractors.archive import compute_content_hash
from bo_semantic_extractor.models import (
    DataProvider,
    ObjectType,
    RawArtifact,
    UniverseObject,
    UniverseSummary,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bo_rest"


def _load_artifact(name: str) -> RawArtifact:
    return RawArtifact.model_validate_json((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _assert_hash_matches_payload(artifact: RawArtifact) -> None:
    canonical = json.dumps(artifact.payload, sort_keys=True).encode("utf-8")
    assert compute_content_hash(canonical) == artifact.content_hash_sha256


# ---------------------------------------------------------------------------
# universe_listing.real_shape.sample.json
# ---------------------------------------------------------------------------


def test_universe_listing_fixture_conforms_to_raw_artifact_envelope() -> None:
    artifact = _load_artifact("universe_listing.real_shape.sample.json")
    _assert_hash_matches_payload(artifact)
    assert artifact.source_system == "BO_QUERY_PANEL_INTERNAL"
    assert artifact.source_operation == "getUniverseList"


def test_universe_listing_real_shape_preserves_known_nesting() -> None:
    """Real shape nests entries under payload["universes"]["universe"] (list), unlike the
    flat placeholder contract in docs/businessobjects_payload_contracts.md."""
    artifact = _load_artifact("universe_listing.real_shape.sample.json")
    entries = artifact.payload["universes"]["universe"]
    assert isinstance(entries, list)
    assert len(entries) == 2
    for entry in entries:
        for field in ("id", "cuid", "name", "description", "type", "subType", "folderId", "path", "pathIds", "revision"):
            assert field in entry


def _map_real_universe_entry_to_summary(entry: dict[str, Any]) -> UniverseSummary:
    """Test-local, demonstrative mapping only — not the production converter.

    Real entries carry a file extension in `name` (e.g. ".unx") and a lowercase `type`; both
    are normalized here purely to prove the fixture is parser-ready.
    """
    name = entry["name"]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return UniverseSummary(
        universe_cuid=entry["cuid"],
        universe_name=stem,
        universe_type=entry["type"].upper(),
        repository_path=entry["path"],
    )


def test_universe_listing_real_shape_is_parser_ready_for_universe_summary() -> None:
    artifact = _load_artifact("universe_listing.real_shape.sample.json")
    entries = artifact.payload["universes"]["universe"]
    summaries = [_map_real_universe_entry_to_summary(entry) for entry in entries]
    assert summaries[0].universe_cuid == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    assert summaries[0].universe_name == "DM_Invoice_Data_Mart"
    assert summaries[0].universe_type == "UNX"


# ---------------------------------------------------------------------------
# query_panel_initialization.real_shape.sample.json
# ---------------------------------------------------------------------------


def test_query_panel_initialization_fixture_conforms_to_raw_artifact_envelope() -> None:
    artifact = _load_artifact("query_panel_initialization.real_shape.sample.json")
    _assert_hash_matches_payload(artifact)
    assert artifact.source_operation == "queryPanelInitialization"


def test_query_panel_initialization_parameter_array_has_prompt_fields() -> None:
    artifact = _load_artifact("query_panel_initialization.real_shape.sample.json")
    parameters = artifact.payload["unvParameterArr"]
    assert len(parameters) == 3
    for parameter in parameters:
        for field in ("question", "name", "dataType", "id"):
            assert field in parameter


def test_query_panel_initialization_prompts_are_parser_ready_for_data_provider() -> None:
    """Demonstrates `unvParameterArr[*].question` can populate `DataProvider.prompts`."""
    artifact = _load_artifact("query_panel_initialization.real_shape.sample.json")
    parameters = artifact.payload["unvParameterArr"]
    prompts = [parameter["question"] for parameter in parameters]
    data_provider = DataProvider(
        document_cuid="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        data_provider_id=str(artifact.payload["id"]),
        data_provider_name=str(artifact.payload["name"]),
        universe_cuid="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        prompts=prompts,
    )
    assert data_provider.prompts == [
        "Enter End Date (MM/DD/YYYY):",
        "Run For Yesterday",
        "Enter Begin Date (MM/DD/YYYY):",
    ]


# ---------------------------------------------------------------------------
# query_panel_outline.real_shape.sample.json
# ---------------------------------------------------------------------------


def test_query_panel_outline_fixture_conforms_to_raw_artifact_envelope() -> None:
    artifact = _load_artifact("query_panel_outline.real_shape.sample.json")
    _assert_hash_matches_payload(artifact)
    assert artifact.source_operation == "queryPanelOutline"


def _walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the recursive outline tree, asserting every node is well-formed along the way."""
    for field in ("name", "child", "objType", "nodes"):
        assert field in node
    flattened = [node]
    for child_node in node["nodes"]:
        flattened.extend(_walk(child_node))
    return flattened


def test_query_panel_outline_tree_is_well_formed_and_preserves_nesting_depth() -> None:
    artifact = _load_artifact("query_panel_outline.real_shape.sample.json")
    all_nodes = _walk(artifact.payload)
    # Root -> "Above Profit Center Hierarchy" -> {"Organization", "Division" -> "Division Desc"}
    assert len(all_nodes) == 5
    leaf_nodes = [node for node in all_nodes if node["child"] is False]
    assert {node["name"] for node in leaf_nodes} == {"Organization", "Division Desc"}


def _map_leaf_node_to_universe_object(node: dict[str, Any], universe_cuid: str) -> UniverseObject:
    """Test-local, demonstrative mapping only — not the production converter.

    `objType`'s real-to-`ObjectType` mapping is unconfirmed, so every node maps to
    `ObjectType.UNKNOWN` rather than guessing (per the skill's "never coerce" rule).
    """
    user_data = node["userData"]
    return UniverseObject(
        universe_cuid=universe_cuid,
        object_id=user_data["b"],
        technical_name=user_data["b"],
        object_name=node["name"],
        folder_path=user_data.get("h", ""),
        object_type=ObjectType.UNKNOWN,
        description=node.get("help"),
        extraction_source="BO_QUERY_PANEL_INTERNAL",
        source_evidence_path="tests/fixtures/bo_rest/query_panel_outline.real_shape.sample.json",
    )


def test_query_panel_outline_leaf_nodes_are_parser_ready_for_universe_object() -> None:
    artifact = _load_artifact("query_panel_outline.real_shape.sample.json")
    all_nodes = _walk(artifact.payload)
    leaf_nodes = [node for node in all_nodes if node["child"] is False]

    objects = [
        _map_leaf_node_to_universe_object(node, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        for node in leaf_nodes
    ]

    assert all(obj.object_type is ObjectType.UNKNOWN for obj in objects)
    organization = next(obj for obj in objects if obj.object_name == "Organization")
    assert organization.object_id == "OBJ_1001"
    assert organization.folder_path == "Profit Center Dimension/Above Profit Center Hierarchy"
