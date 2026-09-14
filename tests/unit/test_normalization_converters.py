"""Unit tests for NORMALIZE-stage converters (placeholder ingestion contract)."""

from __future__ import annotations

import json
from pathlib import Path

from bo_semantic_extractor.models import ObjectType, RawArtifact
from bo_semantic_extractor.normalization.converters import (
    universe_from_raw_artifact,
    universe_objects_from_raw_artifact,
    write_normalized_output,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bo_rest"


def _load_artifact(name: str) -> RawArtifact:
    return RawArtifact.model_validate_json((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_universe_from_raw_artifact_maps_known_fields() -> None:
    artifact = _load_artifact("universe_detail.sample.json")
    universe = universe_from_raw_artifact(artifact)
    assert universe.universe_cuid == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    assert universe.universe_type == "UNX"
    assert universe.connection_ids == ["CONN_SAMPLE_HANA"]


def test_universe_objects_preserves_unknown_type() -> None:
    artifact = _load_artifact("universe_objects.sample.json")
    objects = universe_objects_from_raw_artifact(artifact)
    types = {o.object_id: o.object_type for o in objects}
    assert types["OBJ_0003"] is ObjectType.UNKNOWN
    assert types["OBJ_0002"] is ObjectType.MEASURE
    assert types["OBJ_0001"] is ObjectType.DIMENSION


def test_write_normalized_output_is_sorted_and_schema_valid(tmp_path: Path) -> None:
    universe_artifact = _load_artifact("universe_detail.sample.json")
    objects_artifact = _load_artifact("universe_objects.sample.json")
    universe = universe_from_raw_artifact(universe_artifact)
    objects = universe_objects_from_raw_artifact(objects_artifact)

    paths = write_normalized_output(tmp_path, "run-test-0001", universe, objects)

    assert len(paths) == 2
    objects_json = json.loads(paths[1].read_text(encoding="utf-8"))
    object_ids = [entry["object_id"] for entry in objects_json]
    assert object_ids == sorted(object_ids)
