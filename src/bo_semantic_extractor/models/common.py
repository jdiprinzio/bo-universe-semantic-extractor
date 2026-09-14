"""Shared enums and low-level types used across normalized models and the BO client."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ObjectType(str, Enum):
    """Allowed universe object types. Unknown types must stay UNKNOWN, never be coerced."""

    DIMENSION = "dimension"
    ATTRIBUTE = "attribute"
    MEASURE = "measure"
    FILTER = "filter"
    HIERARCHY = "hierarchy"
    LEVEL = "level"
    PARAMETER = "parameter"
    UNKNOWN = "unknown"


class ReviewStatus(str, Enum):
    """Review lifecycle for AI-proposed semantic enrichment. Never auto-set to APPROVED."""

    AI_PROPOSED = "AI_PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_CHANGES = "NEEDS_CHANGES"


class LineageVerificationStatus(str, Enum):
    """Confidence level for HANA physical-lineage enrichment."""

    VERIFIED = "VERIFIED"
    PARSED_UNVERIFIED = "PARSED_UNVERIFIED"
    UNKNOWN = "UNKNOWN"


class SecurityValidationStatus(str, Enum):
    """Whether an extracted security rule could be validated against a target mapping."""

    VALIDATED = "VALIDATED"
    UNVALIDATED = "UNVALIDATED"
    NOT_FOUND = "NOT_FOUND"


class EvidenceVerificationStatus(str, Enum):
    """Confidence level for a fact extracted from design-artifact evidence (BLX/DFX/HANA).

    Distinct from `LineageVerificationStatus`: `CONFIRMED` means the value is present verbatim
    in a source document (e.g. printed in the BLX/DFX report), not that it has been checked
    against a live system. Only HANA catalog cross-reference can ever justify a physical
    lineage claim beyond `PARSED_UNVERIFIED`.
    """

    CONFIRMED = "CONFIRMED"
    PARSED_UNVERIFIED = "PARSED_UNVERIFIED"
    UNKNOWN = "UNKNOWN"


class UniverseSummary(BaseModel):
    """Lightweight universe listing entry returned by discovery operations."""

    universe_cuid: str
    universe_name: str
    universe_type: str
    repository_path: str


class SourceEvidenceRef(BaseModel):
    """Pointer from a normalized record back to its raw evidence file."""

    raw_path: str
    content_hash_sha256: str


class RawArtifact(BaseModel):
    """An unmodified API/SDK response plus its required evidence metadata."""

    run_id: str
    source_system: str
    source_operation: str
    source_identifier: str
    retrieved_at_utc: datetime
    http_status: int | None = None
    content_hash_sha256: str
    redactions_applied: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw response payload, unmodified except for redactions.",
    )
