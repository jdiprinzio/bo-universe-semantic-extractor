"""JSON Schema generation for normalized models.

Schemas are generated from the Pydantic models in `bo_semantic_extractor.models` so the
checked-in JSON Schema files never drift from the typed models used at runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from bo_semantic_extractor.models import (
    DataProvider,
    PhysicalSource,
    RawArtifact,
    Relationship,
    ReportVariable,
    SecurityRule,
    SemanticEnrichment,
    Universe,
    UniverseObject,
    WebIDocument,
)

MODEL_REGISTRY: dict[str, type[BaseModel]] = {
    "universe": Universe,
    "universe_object": UniverseObject,
    "physical_source": PhysicalSource,
    "relationship": Relationship,
    "webi_document": WebIDocument,
    "data_provider": DataProvider,
    "report_variable": ReportVariable,
    "security_rule": SecurityRule,
    "semantic_enrichment": SemanticEnrichment,
    "raw_artifact": RawArtifact,
}


def build_entity_schemas() -> dict[str, dict[str, Any]]:
    """Return {entity_name: json_schema} for every registered normalized model."""
    return {name: model.model_json_schema() for name, model in MODEL_REGISTRY.items()}


def build_catalog_schema() -> dict[str, Any]:
    """Return a single JSON Schema document describing the full normalized catalog."""
    entity_schemas = build_entity_schemas()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://bo-universe-semantic-extractor/config/catalog_schema.json",
        "title": "BO Universe Semantic Extractor Normalized Catalog",
        "description": (
            "Combined schema for all normalized entities produced by the NORMALIZE stage. "
            "Each entity schema is generated from the corresponding Pydantic model."
        ),
        "type": "object",
        "properties": {name: schema for name, schema in entity_schemas.items()},
    }


def write_schema_files(entity_schema_dir: Path, catalog_schema_path: Path) -> None:
    """Write one JSON Schema file per entity plus the combined catalog schema."""
    entity_schema_dir.mkdir(parents=True, exist_ok=True)
    for name, schema in build_entity_schemas().items():
        (entity_schema_dir / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    catalog_schema_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_schema_path.write_text(
        json.dumps(build_catalog_schema(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    write_schema_files(
        entity_schema_dir=repo_root / "src" / "bo_semantic_extractor" / "normalization" / "schemas",
        catalog_schema_path=repo_root / "config" / "catalog_schema.json",
    )
