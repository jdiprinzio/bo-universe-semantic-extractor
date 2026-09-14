"""Orchestrates BLX/DFX PDF parsing into the five design-artifact catalog CSVs.

No SAP endpoint or SDK call is made — both inputs are the design PDFs already supplied as
evidence (`docs/evidence/`). See `docs/dm_invoice_data_mart_extraction_roadmap.md`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from bo_semantic_extractor.documentation.design_catalog_writer import (
    generate_expression_catalog_csv,
    generate_join_catalog_csv,
    generate_lineage_catalog_csv,
    generate_object_catalog_csv,
    generate_table_catalog_csv,
)
from bo_semantic_extractor.extractors.design_pdf import extract_pdf_text
from bo_semantic_extractor.normalization.business_layer_parser import (
    parse_business_layer_catalogs,
)
from bo_semantic_extractor.normalization.data_foundation_parser import (
    parse_data_foundation_joins,
    parse_data_foundation_tables,
)
from bo_semantic_extractor.normalization.lineage_catalog import build_lineage_catalog


class DesignCatalogSummary(BaseModel):
    """Counts describing one catalog-generation run, for reporting only."""

    object_count: int
    expression_count: int
    table_count: int
    join_count: int
    lineage_count: int
    unresolved_join_count: int
    unresolved_lineage_count: int


def generate_design_catalogs(
    business_layer_pdf: Path,
    data_foundation_pdf: Path,
    output_dir: Path,
) -> DesignCatalogSummary:
    """Parse both design PDFs and write all five catalog CSVs to `output_dir`."""
    blx_text = extract_pdf_text(business_layer_pdf)
    dfx_text = extract_pdf_text(data_foundation_pdf)

    objects, expressions = parse_business_layer_catalogs(blx_text)
    tables = parse_data_foundation_tables(dfx_text)
    joins = parse_data_foundation_joins(dfx_text)
    lineage = build_lineage_catalog(expressions, tables)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "object_catalog.csv").write_text(
        generate_object_catalog_csv(objects), encoding="utf-8"
    )
    (output_dir / "expression_catalog.csv").write_text(
        generate_expression_catalog_csv(expressions), encoding="utf-8"
    )
    (output_dir / "table_catalog.csv").write_text(
        generate_table_catalog_csv(tables), encoding="utf-8"
    )
    (output_dir / "join_catalog.csv").write_text(
        generate_join_catalog_csv(joins), encoding="utf-8"
    )
    (output_dir / "lineage_catalog.csv").write_text(
        generate_lineage_catalog_csv(lineage), encoding="utf-8"
    )

    unresolved_join_count = sum(
        1 for join in joins if join.join_type == "UNKNOWN" or join.cardinality == "UNKNOWN"
    )
    unresolved_lineage_count = sum(
        1 for row in lineage if row.physical_hana_object == "UNKNOWN"
    )

    return DesignCatalogSummary(
        object_count=len(objects),
        expression_count=len(expressions),
        table_count=len(tables),
        join_count=len(joins),
        lineage_count=len(lineage),
        unresolved_join_count=unresolved_join_count,
        unresolved_lineage_count=unresolved_lineage_count,
    )
