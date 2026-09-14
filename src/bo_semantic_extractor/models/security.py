"""Normalized model for extracted security metadata (never inferred from names)."""

from __future__ import annotations

from pydantic import BaseModel

from bo_semantic_extractor.models.common import SecurityValidationStatus


class SecurityRule(BaseModel):
    """A security restriction extracted from BusinessObjects, pending migration mapping."""

    rule_id: str
    universe_cuid: str
    security_type: str
    restricted_resource: str
    source_rule_reference: str
    target_mapping: str | None = None
    validation_status: SecurityValidationStatus = SecurityValidationStatus.UNVALIDATED
