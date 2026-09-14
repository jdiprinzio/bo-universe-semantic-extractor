"""Parser for the BusinessObjects internal Query Panel outline tree.

Source evidence: `docs/evidence/query_panel_outline_raw.json`; sanitized fixture:
`tests/fixtures/bo_rest/query_panel_outline.real_shape.sample.json`. This is the first
production parser for this evidence. It classifies identifier *patterns* (`CLS_*` / `OBJ_*` /
`BJ_*`) and extracts lineage *candidates* from free-text fields — it deliberately does not
assign a semantic `ObjectType` from the raw numeric codes, because that mapping is not yet
confirmed (see `docs/businessobjects_api_requirements.md`).
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from bo_semantic_extractor.models import RawArtifact
from bo_semantic_extractor.models.query_panel_outline_normalized import (
    OutlineClassificationStatus,
    QueryPanelOutlineRecord,
)
from bo_semantic_extractor.models.query_panel_outline_raw import QueryPanelOutlineNode

_CLASS_ID_PREFIX = "CLS_"
_OBJECT_ID_PREFIX = "OBJ_"
_RELATED_ID_PREFIX = "BJ_"

# Detects `table.column`-shaped candidates in free-text fields (e.g. "SAMPLE_DIMENSION.ORG_NAME").
_TABLE_COLUMN_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b")


def parse_query_panel_outline_artifact(artifact: RawArtifact) -> QueryPanelOutlineNode:
    """Validate a RawArtifact's payload as the raw outline tree, preserving every field."""
    return QueryPanelOutlineNode.model_validate(artifact.payload)


def classify_source_node_id(source_node_id: str) -> OutlineClassificationStatus:
    """Classify only the identifier *pattern* of `userData.b` — never its semantic meaning."""
    if source_node_id.startswith(_CLASS_ID_PREFIX):
        return OutlineClassificationStatus.CONFIRMED_CLASS
    if source_node_id.startswith(_OBJECT_ID_PREFIX):
        return OutlineClassificationStatus.CONFIRMED_OBJECT
    return OutlineClassificationStatus.UNKNOWN_IDENTIFIER_PATTERN


def is_confirmed_related_id(related_source_id: str | None) -> bool:
    """Whether `userData.g` matches the confirmed `BJ_*` related-identifier pattern."""
    if related_source_id is None:
        return False
    return related_source_id.startswith(_RELATED_ID_PREFIX)


def extract_lineage_candidates(*texts: str | None) -> list[str]:
    """Detect `table.column`-shaped candidates in `help` / `userData.i`.

    These are unverified candidates only; verification against a real schema happens solely
    in the (separate, optional) ENRICH stage — this function never claims a candidate is a
    real physical column.
    """
    candidates: set[str] = set()
    for text in texts:
        if not text:
            continue
        candidates.update(_TABLE_COLUMN_PATTERN.findall(text))
    return sorted(candidates)


def _join_path(parent_path: str, name: str) -> str:
    return f"{parent_path}/{name}" if parent_path else name


def iter_outline_nodes(
    node: QueryPanelOutlineNode, parent_path: str = ""
) -> Iterator[tuple[QueryPanelOutlineNode, str, str]]:
    """Depth-first, pre-order traversal yielding (node, full_object_path, parent_object_path)."""
    full_path = _join_path(parent_path, node.name)
    yield node, full_path, parent_path
    for child in node.nodes:
        yield from iter_outline_nodes(child, full_path)


def normalize_outline_artifact(artifact: RawArtifact) -> list[QueryPanelOutlineRecord]:
    """Parse and recursively traverse a Query Panel outline RawArtifact into normalized records."""
    root = parse_query_panel_outline_artifact(artifact)
    evidence_path = f"raw/{artifact.run_id}/objects/{artifact.source_identifier}.json"

    records: list[QueryPanelOutlineRecord] = []
    for node, full_path, parent_path in iter_outline_nodes(root):
        user_data = node.userData
        records.append(
            QueryPanelOutlineRecord(
                source_node_id=user_data.b,
                related_source_id=user_data.g,
                object_name=node.name,
                full_object_path=full_path,
                parent_object_path=parent_path or None,
                description=node.help,
                raw_obj_type=node.objType,
                classification_status=classify_source_node_id(user_data.b),
                lineage_candidates=extract_lineage_candidates(node.help, user_data.i),
                source_evidence_path=evidence_path,
            )
        )
    return records
