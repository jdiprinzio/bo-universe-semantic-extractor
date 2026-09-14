"""Parser for the Data Foundation (`.dfx`) design PDF report.

See `docs/dm_invoice_data_mart_design_inventory.md` §3–4 for the confirmed shapes this parser
targets. Join type and cardinality are never present as text in this report (they are icons in
the original PDF) and are always emitted as `"UNKNOWN"` — never guessed.
"""

from __future__ import annotations

import re

from bo_semantic_extractor.extractors.design_pdf import join_block_lines, strip_page_markers
from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.models.design_catalog import (
    DATA_FOUNDATION_SOURCE_SYSTEM,
    JoinCatalogRecord,
    TableCatalogRecord,
)

_TABLE_LINE_PATTERN = re.compile(r"^Table: (.+)$")
_DERIVED_TABLE_LINE_PATTERN = re.compile(r"^Derived Table: (.+)$")
_VIEW_LINE_PATTERN = re.compile(r"^View: (.+)$")
_JOIN_ANCHOR_PATTERN = re.compile(r"^Join(?=\S)", re.MULTILINE)

# Matches the primary "<left>.<col>=<right>.<col>" pair at the start of a join expression;
# left/right may be quoted (e.g. "TODAY_COST (DIM_PROD_COST)") or a plain identifier.
_JOIN_ENDPOINTS_PATTERN = re.compile(
    r'^\s*(?P<left>"[^"]+"|[A-Za-z0-9_]+)\.[A-Za-z0-9_]+\s*=\s*'
    r'(?P<right>"[^"]+"|[A-Za-z0-9_]+)\.[A-Za-z0-9_]+'
)


def parse_data_foundation_tables(text: str) -> list[TableCatalogRecord]:
    """Parse `Table:` / `Derived Table:` / `View:` lines into table catalog records."""
    records: list[TableCatalogRecord] = []
    for line in strip_page_markers(text).splitlines():
        line = line.strip()
        if not line:
            continue
        if match := _DERIVED_TABLE_LINE_PATTERN.match(line):
            records.append(
                TableCatalogRecord(
                    table_name=match.group(1).strip(),
                    table_type="derived",
                    source_system=DATA_FOUNDATION_SOURCE_SYSTEM,
                    verification_status=EvidenceVerificationStatus.CONFIRMED,
                )
            )
        elif match := _VIEW_LINE_PATTERN.match(line):
            records.append(
                TableCatalogRecord(
                    table_name=match.group(1).strip(),
                    table_type="view",
                    source_system=DATA_FOUNDATION_SOURCE_SYSTEM,
                    verification_status=EvidenceVerificationStatus.CONFIRMED,
                )
            )
        elif match := _TABLE_LINE_PATTERN.match(line):
            records.append(
                TableCatalogRecord(
                    table_name=match.group(1).strip(),
                    table_type="UNKNOWN",
                    source_system=DATA_FOUNDATION_SOURCE_SYSTEM,
                    verification_status=EvidenceVerificationStatus.CONFIRMED,
                )
            )
    return records


def parse_data_foundation_joins(text: str) -> list[JoinCatalogRecord]:
    """Parse `Join<expression>` entries into join catalog records, numbered in document order.

    Join expressions can wrap across multiple extracted-PDF lines (e.g. a quoted derived-table
    name split mid-parenthesis), so entries are located by anchor (`Join` at the start of a
    line, immediately followed by a non-space character) and joined into one string up to the
    next anchor — never processed one raw line at a time.
    """
    cleaned = strip_page_markers(text)
    anchors = list(_JOIN_ANCHOR_PATTERN.finditer(cleaned))
    # The Joins section is always followed by a Tables/Views section; without this boundary the
    # last join's block would otherwise run to the end of the document.
    section_end_match = re.search(r"^(Tables|Views) \(", cleaned, re.MULTILINE)
    section_end = section_end_match.start() if section_end_match else len(cleaned)

    records: list[JoinCatalogRecord] = []
    join_id = 0
    for index, anchor in enumerate(anchors):
        block_start = anchor.end()
        next_anchor_start = anchors[index + 1].start() if index + 1 < len(anchors) else len(cleaned)
        block_end = min(next_anchor_start, section_end) if section_end > block_start else next_anchor_start
        join_expression = join_block_lines(cleaned[block_start:block_end])
        if "=" not in join_expression:
            continue  # The "Joins (N)" section header also matches the anchor; skip it.

        join_id += 1
        endpoints = _JOIN_ENDPOINTS_PATTERN.match(join_expression)
        if endpoints:
            left_object = endpoints.group("left")
            right_object = endpoints.group("right")
            status = EvidenceVerificationStatus.CONFIRMED
        else:
            left_object = "UNKNOWN"
            right_object = "UNKNOWN"
            status = EvidenceVerificationStatus.PARSED_UNVERIFIED
        records.append(
            JoinCatalogRecord(
                join_id=str(join_id),
                left_object=left_object,
                right_object=right_object,
                join_expression=join_expression,
                join_type="UNKNOWN",
                cardinality="UNKNOWN",
                verification_status=status,
            )
        )
    return records
