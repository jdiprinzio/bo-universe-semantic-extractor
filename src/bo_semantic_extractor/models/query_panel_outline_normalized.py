"""Normalized (but not yet semantically typed) records produced by the Query Panel outline parser.

Deliberately distinct from `UniverseObject`: these records classify identifier *patterns*
(`CLS_*` / `OBJ_*` / `BJ_*`) and extract lineage *candidates* only. They never assign a
semantic `ObjectType` from the raw numeric codes (`objType`, `userData.c`, `userData.s`),
because that mapping is not yet confirmed — see `docs/businessobjects_api_requirements.md`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OutlineClassificationStatus(str, Enum):
    """Confidence in a node's identifier *pattern* only — never its semantic meaning."""

    CONFIRMED_CLASS = "CONFIRMED_CLASS"
    CONFIRMED_OBJECT = "CONFIRMED_OBJECT"
    UNKNOWN_IDENTIFIER_PATTERN = "UNKNOWN_IDENTIFIER_PATTERN"


class QueryPanelOutlineRecord(BaseModel):
    """One flattened, path-aware record derived from a single Query Panel outline node."""

    source_node_id: str
    related_source_id: str | None = None
    object_name: str
    full_object_path: str
    parent_object_path: str | None = None
    description: str | None = None
    raw_obj_type: int
    classification_status: OutlineClassificationStatus
    lineage_candidates: list[str] = Field(default_factory=list)
    source_evidence_path: str
