"""Typed validation findings produced by the VALIDATE stage."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class FindingSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class FindingCategory(str, Enum):
    DUPLICATE_OBJECT_NAME = "DUPLICATE_OBJECT_NAME"
    MISSING_DESCRIPTION = "MISSING_DESCRIPTION"
    UNKNOWN_OBJECT_TYPE = "UNKNOWN_OBJECT_TYPE"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    MISSING_RAW_EVIDENCE = "MISSING_RAW_EVIDENCE"


class ValidationFinding(BaseModel):
    """A single, explicit validation finding tied to a specific object where applicable."""

    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    message: str
    universe_cuid: str
    object_id: str | None = None
