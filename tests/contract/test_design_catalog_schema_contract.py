"""Contract tests validating the five design-catalog CSV schemas against real evidence.

Runs the full BLX/DFX PDF -> catalog pipeline against the actual evidence documents already
committed under `docs/evidence/`, and asserts each CSV's header/columns and
`verification_status` values conform to contract — independent of exact row counts, which may
shift slightly as the parser is refined but must never regress the schema itself.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bo_semantic_extractor.normalization.design_catalog_pipeline import generate_design_catalogs

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / ".." / "docs" / "evidence"
BLX_PDF = (EVIDENCE_DIR / "DM_Invoice_Data_Mart_blx.pdf").resolve()
DFX_PDF = (EVIDENCE_DIR / "DM_Invoice_Data_Mart_dfx.pdf").resolve()

_ALLOWED_STATUSES = {"CONFIRMED", "PARSED_UNVERIFIED", "UNKNOWN"}

_EXPECTED_COLUMNS = {
    "object_catalog.csv": [
        "object_id", "object_name", "object_type", "folder_path", "description",
        "source_system", "verification_status",
    ],
    "expression_catalog.csv": [
        "object_id", "object_name", "select_expression", "where_expression",
        "projection_function", "source_system", "verification_status",
    ],
    "table_catalog.csv": ["table_name", "table_type", "source_system", "verification_status"],
    "join_catalog.csv": [
        "join_id", "left_object", "right_object", "join_expression", "join_type",
        "cardinality", "verification_status",
    ],
    "lineage_catalog.csv": [
        "object_name", "object_id", "select_expression", "referenced_table",
        "referenced_column", "physical_hana_object", "physical_hana_column",
        "verification_status",
    ],
}

pytestmark = pytest.mark.skipif(
    not (BLX_PDF.exists() and DFX_PDF.exists()),
    reason="Real DM_Invoice_Data_Mart evidence PDFs are not present in this checkout.",
)


@pytest.fixture(scope="module")
def generated_catalog_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output_dir = tmp_path_factory.mktemp("design_catalogs")
    generate_design_catalogs(BLX_PDF, DFX_PDF, output_dir)
    return output_dir


@pytest.mark.parametrize("filename", list(_EXPECTED_COLUMNS))
def test_catalog_file_exists_with_exact_column_order(
    generated_catalog_dir: Path, filename: str
) -> None:
    path = generated_catalog_dir / filename
    assert path.exists()
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert header == _EXPECTED_COLUMNS[filename]


@pytest.mark.parametrize("filename", list(_EXPECTED_COLUMNS))
def test_every_row_has_an_allowed_verification_status(
    generated_catalog_dir: Path, filename: str
) -> None:
    path = generated_catalog_dir / filename
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, f"{filename} produced zero rows"
    assert all(row["verification_status"] in _ALLOWED_STATUSES for row in rows)


def test_object_catalog_row_count_matches_confirmed_inventory(generated_catalog_dir: Path) -> None:
    with (generated_catalog_dir / "object_catalog.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts_by_type: dict[str, int] = {}
    for row in rows:
        counts_by_type[row["object_type"]] = counts_by_type.get(row["object_type"], 0) + 1
    # Confirmed exact counts from docs/dm_invoice_data_mart_design_inventory.md.
    assert counts_by_type["class"] == 204
    assert counts_by_type["dimension"] == 925
    assert counts_by_type["attribute"] == 179
    assert counts_by_type["measure"] == 785


def test_table_catalog_includes_confirmed_table_count(generated_catalog_dir: Path) -> None:
    with (generated_catalog_dir / "table_catalog.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    # The DFX Statistics block's "Table 38" already includes the 3 derived tables (35 plain
    # "Table:" entries + 3 "Derived Table:" entries = 38); + 1 view = 39 total catalog rows.
    assert len(rows) == 39


def test_join_catalog_has_34_joins_all_unresolved_type_and_cardinality(
    generated_catalog_dir: Path,
) -> None:
    with (generated_catalog_dir / "join_catalog.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 34
    assert all(row["join_type"] == "UNKNOWN" for row in rows)
    assert all(row["cardinality"] == "UNKNOWN" for row in rows)


def test_lineage_catalog_never_fabricates_hana_mappings(generated_catalog_dir: Path) -> None:
    with (generated_catalog_dir / "lineage_catalog.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, "lineage_catalog.csv produced zero rows"
    assert all(row["physical_hana_object"] == "UNKNOWN" for row in rows)
    assert all(row["physical_hana_column"] == "UNKNOWN" for row in rows)
