"""Typed catalog records for the DM_Invoice_Data_Mart design-artifact extraction (BLX/DFX PDFs).

Column order on each model matches the requested CSV column order exactly. Every field is
either taken verbatim from the source evidence (`CONFIRMED`), derived via unverified pattern
detection (`PARSED_UNVERIFIED`), or explicitly `UNKNOWN` — never guessed or fabricated. See
`docs/dm_invoice_data_mart_extraction_roadmap.md`.
"""

from __future__ import annotations

from pydantic import BaseModel

from bo_semantic_extractor.models.common import EvidenceVerificationStatus

BUSINESS_LAYER_SOURCE_SYSTEM = "BO_BUSINESS_LAYER_DESIGN_PDF"
DATA_FOUNDATION_SOURCE_SYSTEM = "BO_DATA_FOUNDATION_DESIGN_PDF"


class ObjectCatalogRecord(BaseModel):
    """One row per Business Layer object (class/dimension/attribute/measure/filter)."""

    object_id: str
    object_name: str
    object_type: str
    folder_path: str | None = None
    description: str | None = None
    source_system: str
    verification_status: EvidenceVerificationStatus


class ExpressionCatalogRecord(BaseModel):
    """One row per Business Layer object's Select/Where expression and projection metadata."""

    object_id: str
    object_name: str
    select_expression: str | None = None
    where_expression: str | None = None
    projection_function: str | None = None
    source_system: str
    verification_status: EvidenceVerificationStatus


class TableCatalogRecord(BaseModel):
    """One row per Data Foundation table/derived table/view."""

    table_name: str
    table_type: str
    source_system: str
    verification_status: EvidenceVerificationStatus


class JoinCatalogRecord(BaseModel):
    """One row per Data Foundation join."""

    join_id: str
    left_object: str
    right_object: str
    join_expression: str
    join_type: str
    cardinality: str
    verification_status: EvidenceVerificationStatus


class LineageCatalogRecord(BaseModel):
    """One row per Business-Object-to-candidate-physical-column lineage candidate.

    `physical_hana_object`/`physical_hana_column` are always `"UNKNOWN"` in this stage — no
    HANA catalog cross-reference has been performed, and none is fabricated here.
    """

    object_name: str
    object_id: str
    select_expression: str | None = None
    referenced_table: str | None = None
    referenced_column: str | None = None
    physical_hana_object: str = "UNKNOWN"
    physical_hana_column: str = "UNKNOWN"
    verification_status: EvidenceVerificationStatus
