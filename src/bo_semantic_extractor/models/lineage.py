"""Normalized models for physical source references and join/context relationships."""

from __future__ import annotations

from pydantic import BaseModel


class PhysicalSource(BaseModel):
    """A physical table/column referenced by a universe object, prior to lineage verification."""

    source_id: str
    source_platform: str
    database_name: str | None = None
    schema_name: str | None = None
    object_name: str
    object_type: str
    column_name: str | None = None
    evidence: str


class Relationship(BaseModel):
    """A join or context relationship between two physical sources."""

    relationship_id: str
    left_source_id: str
    right_source_id: str
    join_expression: str
    join_type: str
    cardinality: str | None = None
    context_name: str | None = None
    is_shortcut: bool = False
    extraction_source: str
    evidence: str
