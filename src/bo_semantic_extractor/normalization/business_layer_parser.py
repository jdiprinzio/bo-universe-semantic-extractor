"""Parser for the Business Layer (`.blx`) design PDF report.

See `docs/dm_invoice_data_mart_design_inventory.md` for the confirmed block/field shapes this
parser targets, and `docs/dm_invoice_data_mart_extraction_roadmap.md` §1.1 for the extraction
approach. Every field is read from the report text as-is; unresolved fields are `None` (never
guessed), and object rows without a confirmed `Cuid` are marked `UNKNOWN`.
"""

from __future__ import annotations

import re

from bo_semantic_extractor.extractors.design_pdf import (
    extract_sequential_fields,
    join_block_lines,
)
from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.models.design_catalog import (
    BUSINESS_LAYER_SOURCE_SYSTEM,
    ExpressionCatalogRecord,
    ObjectCatalogRecord,
)

_BLOCK_HEADER_PATTERN = re.compile(
    r"^(Folder|Dimension|Attribute|Measure|Filter): (.+)$", re.MULTILINE
)

_HEADING_TO_OBJECT_TYPE = {
    "Folder": "class",
    "Dimension": "dimension",
    "Attribute": "attribute",
    "Measure": "measure",
    "Filter": "filter",
}

_FIELD_LABELS_BY_HEADING = {
    "Folder": ["Name", "Description", "Cuid", "Translation ID", "Path", "State"],
    "Dimension": [
        "Name", "Description", "Cuid", "Translation ID", "Path", "State", "Data Type",
        "Aggregatable", "SQL Definition", "Select", "Advanced",
        "Minimum Object Level Security", "Data Sensitivity Category", "List of Values",
        "Can be used in",
    ],
    "Attribute": [
        "Name", "Description", "Cuid", "Translation ID", "Path", "State", "Data Type",
        "Aggregatable", "SQL Definition", "Select", "Advanced",
        "Minimum Object Level Security", "Data Sensitivity Category", "List of Values",
        "Can be used in",
    ],
    "Measure": [
        "Name", "Description", "Cuid", "Translation ID", "Path", "State", "Data Type",
        "Projection Function", "High Precision", "SQL Definition", "Select", "Advanced",
        "Minimum Object Level Security", "Data Sensitivity Category", "Can be used in",
    ],
    "Filter": [
        "Name", "Description", "Cuid", "Translation ID", "Path", "State", "Filter type",
        "Where expression",
    ],
}


def _iter_blocks(text: str) -> list[tuple[str, str, str]]:
    """Split BLX text into (heading, header_name, block_text) triples."""
    matches = list(_BLOCK_HEADER_PATTERN.finditer(text))
    blocks: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(1)
        header_name = match.group(2).strip()
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((heading, header_name, text[block_start:block_end]))
    return blocks


def parse_business_layer_catalogs(
    text: str,
) -> tuple[list[ObjectCatalogRecord], list[ExpressionCatalogRecord]]:
    """Parse BLX report text into object and expression catalog records."""
    objects: list[ObjectCatalogRecord] = []
    expressions: list[ExpressionCatalogRecord] = []

    for heading, header_name, block_text in _iter_blocks(text):
        object_type = _HEADING_TO_OBJECT_TYPE[heading]
        joined = join_block_lines(block_text)
        fields = extract_sequential_fields(joined, _FIELD_LABELS_BY_HEADING[heading])

        object_id = fields.get("Cuid") or "UNKNOWN"
        object_name = fields.get("Name") or header_name
        object_status = (
            EvidenceVerificationStatus.CONFIRMED
            if fields.get("Cuid")
            else EvidenceVerificationStatus.UNKNOWN
        )
        objects.append(
            ObjectCatalogRecord(
                object_id=object_id,
                object_name=object_name,
                object_type=object_type,
                folder_path=fields.get("Path") or None,
                description=fields.get("Description") or None,
                source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
                verification_status=object_status,
            )
        )

        if object_type == "class":
            continue  # Folders/classes carry no Select/Where expression.

        select_expression = fields.get("Select") or None
        where_expression = fields.get("Where expression") or None
        projection_function = fields.get("Projection Function") or None
        expression_status = (
            EvidenceVerificationStatus.CONFIRMED
            if (select_expression or where_expression)
            else EvidenceVerificationStatus.UNKNOWN
        )
        expressions.append(
            ExpressionCatalogRecord(
                object_id=object_id,
                object_name=object_name,
                select_expression=select_expression,
                where_expression=where_expression,
                projection_function=projection_function,
                source_system=BUSINESS_LAYER_SOURCE_SYSTEM,
                verification_status=expression_status,
            )
        )

    return objects, expressions
