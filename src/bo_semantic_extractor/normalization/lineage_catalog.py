"""Builds `lineage_catalog.csv` rows from parsed Business Layer expressions.

Lineage here means **candidate** `table.column` references detected by pattern in a Select or
Where expression — never a verified physical mapping. A candidate is `PARSED_UNVERIFIED` only
when its table name matches a name already confirmed in the Data Foundation table catalog;
otherwise it is `UNKNOWN`. `physical_hana_object`/`physical_hana_column` are always `"UNKNOWN"`
here — no HANA catalog cross-reference is performed by this module.
"""

from __future__ import annotations

import re

from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.models.design_catalog import (
    ExpressionCatalogRecord,
    LineageCatalogRecord,
    TableCatalogRecord,
)

# Business-object cross-references use "\"-delimited paths (e.g. @Select(Date Dimension\Year)),
# so a literal "." always separates a physical table name from a column name in this evidence.
_TABLE_COLUMN_PATTERN = re.compile(r'("[^"]+"|\b[A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b')


def extract_table_column_candidates(text: str) -> list[tuple[str, str]]:
    """Detect `table.column`-shaped candidates in a raw expression, preserving order, deduped."""
    seen: set[tuple[str, str]] = set()
    candidates: list[tuple[str, str]] = []
    for table, column in _TABLE_COLUMN_PATTERN.findall(text):
        table_clean = table.strip('"')
        key = (table_clean, column)
        if key not in seen:
            seen.add(key)
            candidates.append(key)
    return candidates


def build_lineage_catalog(
    expressions: list[ExpressionCatalogRecord],
    tables: list[TableCatalogRecord],
) -> list[LineageCatalogRecord]:
    """Build lineage candidate rows for every expression with a detectable table.column pattern."""
    known_table_names = {table.table_name for table in tables}
    records: list[LineageCatalogRecord] = []

    for expression in expressions:
        source_text = expression.select_expression or expression.where_expression
        if not source_text:
            continue
        for table_name, column_name in extract_table_column_candidates(source_text):
            status = (
                EvidenceVerificationStatus.PARSED_UNVERIFIED
                if table_name in known_table_names
                else EvidenceVerificationStatus.UNKNOWN
            )
            records.append(
                LineageCatalogRecord(
                    object_name=expression.object_name,
                    object_id=expression.object_id,
                    select_expression=source_text,
                    referenced_table=table_name,
                    referenced_column=column_name,
                    verification_status=status,
                )
            )
    return records
