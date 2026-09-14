"""CSV generators for the DM_Invoice_Data_Mart design-artifact catalogs.

Column order matches each catalog's requested schema exactly; rows are sorted by a stable
identifier, never by display name alone.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from typing import TypeVar

from pydantic import BaseModel

from bo_semantic_extractor.models.design_catalog import (
    ExpressionCatalogRecord,
    JoinCatalogRecord,
    LineageCatalogRecord,
    ObjectCatalogRecord,
    TableCatalogRecord,
)

_ModelT = TypeVar("_ModelT", bound=BaseModel)

OBJECT_CATALOG_COLUMNS = [
    "object_id", "object_name", "object_type", "folder_path", "description",
    "source_system", "verification_status",
]
EXPRESSION_CATALOG_COLUMNS = [
    "object_id", "object_name", "select_expression", "where_expression",
    "projection_function", "source_system", "verification_status",
]
TABLE_CATALOG_COLUMNS = ["table_name", "table_type", "source_system", "verification_status"]
JOIN_CATALOG_COLUMNS = [
    "join_id", "left_object", "right_object", "join_expression", "join_type",
    "cardinality", "verification_status",
]
LINEAGE_CATALOG_COLUMNS = [
    "object_name", "object_id", "select_expression", "referenced_table", "referenced_column",
    "physical_hana_object", "physical_hana_column", "verification_status",
]


def _write_csv(records: Sequence[_ModelT], columns: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for record in records:
        row = record.model_dump(mode="json")
        writer.writerow({column: row[column] for column in columns})
    return buffer.getvalue()


def generate_object_catalog_csv(records: list[ObjectCatalogRecord]) -> str:
    return _write_csv(sorted(records, key=lambda r: r.object_id), OBJECT_CATALOG_COLUMNS)


def generate_expression_catalog_csv(records: list[ExpressionCatalogRecord]) -> str:
    return _write_csv(sorted(records, key=lambda r: r.object_id), EXPRESSION_CATALOG_COLUMNS)


def generate_table_catalog_csv(records: list[TableCatalogRecord]) -> str:
    return _write_csv(sorted(records, key=lambda r: r.table_name), TABLE_CATALOG_COLUMNS)


def generate_join_catalog_csv(records: list[JoinCatalogRecord]) -> str:
    return _write_csv(sorted(records, key=lambda r: int(r.join_id)), JOIN_CATALOG_COLUMNS)


def generate_lineage_catalog_csv(records: list[LineageCatalogRecord]) -> str:
    return _write_csv(
        sorted(records, key=lambda r: (r.object_id, r.referenced_table or "")),
        LINEAGE_CATALOG_COLUMNS,
    )
