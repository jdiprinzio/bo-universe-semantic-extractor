"""Raw, unmodified shape of the BusinessObjects internal Query Panel outline tree.

Source: BusinessObjects' internal Query Panel service (`source_system="BO_QUERY_PANEL_INTERNAL"`
in the `RawArtifact` envelope) — **not** the officially documented `/biprws/` REST API. See
`docs/businessobjects_api_requirements.md`. Field names and types mirror the raw JSON exactly
(evidence: `docs/evidence/query_panel_outline_raw.json`); unknown/future fields are preserved
via `extra="allow"` rather than silently dropped.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QueryPanelOutlineUserData(BaseModel):
    """Raw `userData` object attached to every outline node.

    Keys are undocumented by SAP and were reverse-engineered from evidence. Known keys:
    `b` = object/class identifier (`CLS_*` / `OBJ_*` confirmed patterns), `c` = numeric type
    code (not yet mapped to a semantic type), `g` = related identifier (`BJ_*` confirmed
    pattern), `h` = parent folder path, `i` = description/tooltip text, `j` = numeric flag
    (not yet mapped), `s` = numeric qualification code (not yet mapped).
    """

    model_config = ConfigDict(extra="allow")

    b: str
    c: int
    g: str | None = None
    h: str | None = None
    i: str | None = None
    j: int | None = None
    s: int | None = None


class QueryPanelOutlineNode(BaseModel):
    """Raw outline tree node.

    Used for both the root node and every nested child node — the real API returns an
    identical shape at every depth (evidence has no separate "root" schema).
    """

    model_config = ConfigDict(extra="allow")

    name: str
    child: bool
    objType: int
    help: str | None = None
    userData: QueryPanelOutlineUserData
    nodes: list[QueryPanelOutlineNode] = Field(default_factory=list)
