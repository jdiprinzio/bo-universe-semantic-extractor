"""NORMALIZE stage: convert archived raw evidence into typed, versioned models.

The exact SAP BI Semantic Layer REST payload shape has not yet been confirmed for this
environment (see `bo_client/rest_client.py`). The mapping functions below target a
placeholder ingestion contract matching the sanitized fixtures under
`tests/fixtures/bo_rest/` — update them once the true SAP payload shape is confirmed.
Unrecognized fields are never guessed: missing values normalize to `None`/`unknown`.
"""

from __future__ import annotations

import json
from pathlib import Path

from bo_semantic_extractor.models import ObjectType, RawArtifact, Universe, UniverseObject

_KNOWN_OBJECT_TYPES = {object_type.value for object_type in ObjectType}


def universe_from_raw_artifact(artifact: RawArtifact) -> Universe:
    """Map a `getUniverse`-shaped RawArtifact to a typed `Universe` (placeholder contract)."""
    payload = artifact.payload
    return Universe(
        universe_cuid=payload["cuid"],
        universe_name=payload["name"],
        universe_type=payload.get("type", "unknown"),
        repository_path=payload.get("path", ""),
        description=payload.get("description"),
        connection_ids=list(payload.get("connections", [])),
        source_system=artifact.source_system,
        extracted_at_utc=artifact.retrieved_at_utc,
    )


def universe_objects_from_raw_artifact(artifact: RawArtifact) -> list[UniverseObject]:
    """Map a `listUniverseObjects`-shaped RawArtifact to typed `UniverseObject`s.

    Unrecognized `type` values are preserved as `ObjectType.UNKNOWN`, never coerced to the
    closest known type.
    """
    universe_cuid = artifact.source_identifier
    objects: list[UniverseObject] = []
    for raw_object in artifact.payload.get("objects", []):
        raw_type = raw_object.get("type", "unknown")
        object_type = (
            ObjectType(raw_type) if raw_type in _KNOWN_OBJECT_TYPES else ObjectType.UNKNOWN
        )
        objects.append(
            UniverseObject(
                universe_cuid=universe_cuid,
                object_id=raw_object["id"],
                technical_name=raw_object.get("technical_name", raw_object["id"]),
                object_name=raw_object.get("name", raw_object["id"]),
                folder_path=raw_object.get("folder", ""),
                object_type=object_type,
                description=raw_object.get("description"),
                data_type=raw_object.get("data_type"),
                select_expression=raw_object.get("select"),
                where_expression=raw_object.get("where"),
                aggregation_function=raw_object.get("aggregation"),
                extraction_source=artifact.source_system,
                source_evidence_path=(
                    f"raw/{artifact.run_id}/objects/{artifact.source_identifier}.json"
                ),
            )
        )
    return objects


def write_normalized_output(
    normalized_root: Path,
    run_id: str,
    universe: Universe,
    objects: list[UniverseObject],
) -> list[Path]:
    """Write deterministic, UTF-8, schema-validated normalized JSON for one run.

    Records are sorted by stable identifiers (`object_id`), not display names.
    """
    run_dir = normalized_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    universe_path = run_dir / "universe.json"
    universe_path.write_text(universe.model_dump_json(indent=2), encoding="utf-8")

    sorted_objects = sorted(objects, key=lambda o: o.object_id)
    objects_path = run_dir / "objects.json"
    objects_path.write_text(
        json.dumps(
            [o.model_dump(mode="json") for o in sorted_objects], indent=2, sort_keys=True
        ),
        encoding="utf-8",
    )

    # Validate the just-written output against its schema before declaring success.
    Universe.model_validate_json(universe_path.read_text(encoding="utf-8"))
    for entry in json.loads(objects_path.read_text(encoding="utf-8")):
        UniverseObject.model_validate(entry)

    return [universe_path, objects_path]
