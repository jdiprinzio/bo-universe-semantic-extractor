"""Normalized models for a published universe and its objects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bo_semantic_extractor.models.common import ObjectType


class Universe(BaseModel):
    """A published SAP BusinessObjects universe (UNX or UNV)."""

    universe_cuid: str
    universe_name: str
    universe_type: str = Field(description="'UNX' or 'UNV'.")
    repository_path: str
    description: str | None = None
    connection_ids: list[str] = Field(default_factory=list)
    source_system: str
    extracted_at_utc: datetime


class UniverseObject(BaseModel):
    """A single semantic-layer object (dimension, measure, filter, etc.) within a universe."""

    universe_cuid: str
    object_id: str
    technical_name: str
    object_name: str
    folder_path: str
    object_type: ObjectType
    description: str | None = None
    data_type: str | None = None
    select_expression: str | None = None
    where_expression: str | None = None
    aggregation_function: str | None = None
    projection_function: str | None = None
    associated_dimension_id: str | None = None
    list_of_values_id: str | None = None
    is_hidden: bool = False
    is_deprecated: bool = False
    access_level: str | None = None
    extraction_source: str
    source_evidence_path: str
