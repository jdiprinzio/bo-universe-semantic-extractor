"""Typed normalized models for the semantic extraction pipeline.

Import from this package rather than individual submodules where practical, e.g.::

    from bo_semantic_extractor.models import Universe, UniverseObject
"""

from __future__ import annotations

from bo_semantic_extractor.models.common import (
    EvidenceVerificationStatus,
    LineageVerificationStatus,
    ObjectType,
    RawArtifact,
    ReviewStatus,
    SecurityValidationStatus,
    SourceEvidenceRef,
    UniverseSummary,
)
from bo_semantic_extractor.models.design_catalog import (
    BUSINESS_LAYER_SOURCE_SYSTEM,
    DATA_FOUNDATION_SOURCE_SYSTEM,
    ExpressionCatalogRecord,
    JoinCatalogRecord,
    LineageCatalogRecord,
    ObjectCatalogRecord,
    TableCatalogRecord,
)
from bo_semantic_extractor.models.enrichment import SemanticEnrichment
from bo_semantic_extractor.models.lineage import PhysicalSource, Relationship
from bo_semantic_extractor.models.query_panel_outline_normalized import (
    OutlineClassificationStatus,
    QueryPanelOutlineRecord,
)
from bo_semantic_extractor.models.query_panel_outline_raw import (
    QueryPanelOutlineNode,
    QueryPanelOutlineUserData,
)
from bo_semantic_extractor.models.security import SecurityRule
from bo_semantic_extractor.models.universe import Universe, UniverseObject
from bo_semantic_extractor.models.webi import DataProvider, ReportVariable, WebIDocument

__all__ = [
    "BUSINESS_LAYER_SOURCE_SYSTEM",
    "DATA_FOUNDATION_SOURCE_SYSTEM",
    "DataProvider",
    "EvidenceVerificationStatus",
    "ExpressionCatalogRecord",
    "JoinCatalogRecord",
    "LineageCatalogRecord",
    "LineageVerificationStatus",
    "ObjectCatalogRecord",
    "ObjectType",
    "OutlineClassificationStatus",
    "PhysicalSource",
    "QueryPanelOutlineNode",
    "QueryPanelOutlineRecord",
    "QueryPanelOutlineUserData",
    "RawArtifact",
    "Relationship",
    "ReportVariable",
    "ReviewStatus",
    "SecurityRule",
    "SecurityValidationStatus",
    "SemanticEnrichment",
    "SourceEvidenceRef",
    "TableCatalogRecord",
    "Universe",
    "UniverseObject",
    "UniverseSummary",
    "WebIDocument",
]
