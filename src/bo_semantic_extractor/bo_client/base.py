"""Client-agnostic interface for read-only access to the BO semantic layer.

Implementations (REST, SDK-backed, or test doubles) must conform to this Protocol so
extraction logic never depends on a specific transport.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from bo_semantic_extractor.models import RawArtifact, UniverseSummary


@runtime_checkable
class SemanticLayerClient(Protocol):
    """Read-only operations required by the DISCOVER and EXTRACT pipeline stages."""

    def list_universes(self) -> list[UniverseSummary]:
        """List universes visible to the authenticated user."""
        ...

    def get_universe(self, universe_cuid: str) -> RawArtifact:
        """Fetch the raw universe record for a given CUID."""
        ...

    def list_universe_objects(self, universe_cuid: str) -> list[RawArtifact]:
        """Fetch raw universe object records (dimensions, measures, filters, etc.)."""
        ...

    def list_dependent_documents(self, universe_cuid: str) -> list[RawArtifact]:
        """List Web Intelligence documents that depend on the given universe."""
        ...

    def get_document_metadata(self, document_cuid: str) -> RawArtifact:
        """Fetch raw metadata (data providers, variables, prompts) for a WebI document."""
        ...
