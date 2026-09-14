"""EXTRACT stage: fetch raw universe, object, and (optionally) WebI records."""

from __future__ import annotations

from bo_semantic_extractor.bo_client.base import SemanticLayerClient
from bo_semantic_extractor.config import ExtractionSettings
from bo_semantic_extractor.models import RawArtifact


def extract_universe_artifacts(
    client: SemanticLayerClient,
    universe_cuid: str,
    extraction_settings: ExtractionSettings,
) -> list[RawArtifact]:
    """Fetch raw universe + object records, and optionally dependent WebI documents."""
    artifacts: list[RawArtifact] = [client.get_universe(universe_cuid)]
    artifacts.extend(client.list_universe_objects(universe_cuid))

    if extraction_settings.include_webi_dependencies:
        documents = client.list_dependent_documents(universe_cuid)
        artifacts.extend(documents)
        for document in documents[: extraction_settings.max_documents]:
            artifacts.append(client.get_document_metadata(document.source_identifier))

    return artifacts
