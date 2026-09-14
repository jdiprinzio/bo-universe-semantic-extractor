"""Unit tests for the Business Layer (.blx) PDF parser, using synthetic report-shaped text."""

from __future__ import annotations

from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.normalization.business_layer_parser import (
    parse_business_layer_catalogs,
)

SAMPLE_BLX_TEXT = """
Folder: Sample Dimension Folder
Name Sample Dimension Folder
Cuid CLS_1
Translation ID CLS_1
Path \\Sample Dimension Folder\\
State Active
Dimension: Sample Date
Name Sample Date
Description Sample Date : SAMPLE_TABLE.SAMPLE_DATE_COL
Cuid OBJ_1
Translation ID OBJ_1
Path \\Sample Dimension Folder\\
State Active
Data Type DateTime
SQL Definition
Select SAMPLE_TABLE.SAMPLE_DATE_COL
Advanced
Minimum Object Level Security Public
Data Sensitivity Category Uncategorized data
List of Values Editable
Can be used in Results, Filters, Sorts
Attribute: Sample Attribute
Name Sample Attribute
Description Sample attribute description
Cuid OBJ_2
Translation ID OBJ_2
Path \\Sample Dimension Folder\\
State Active
Data Type String
Aggregatable True
SQL Definition
Select SAMPLE_TABLE.SAMPLE_ATTR_COL
Advanced
Minimum Object Level Security Public
Data Sensitivity Category Uncategorized data
Can be used in Results, Filters, Sorts
Measure: Sample Measure
Name Sample Measure
Description Sample measure description
Cuid OBJ_3
Translation ID OBJ_3
Path \\Measures\\
State Active
Data Type Numeric
Projection Function Sum
High Precision False
SQL Definition
Select SUM(SAMPLE_FACT.SAMPLE_AMT)
Advanced
Minimum Object Level Security Public
Data Sensitivity Category Uncategorized data
Can be used in Results, Filters, Sorts
Filter: Sample Filter
Name Sample Filter
Description Sample filter description
Cuid FIL_1
Translation ID FIL_1
Path \\Filters\\
State Active
Filter type NATIVE
Where expression SAMPLE_TABLE.SAMPLE_FLAG = 'Y'
"""


def test_parses_all_five_object_types() -> None:
    objects, _expressions = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    assert {o.object_type for o in objects} == {"class", "dimension", "attribute", "measure", "filter"}
    assert len(objects) == 5


def test_class_objects_have_no_expression_row() -> None:
    _objects, expressions = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    assert len(expressions) == 4  # dimension + attribute + measure + filter, not the class


def test_object_ids_and_names_are_extracted_correctly() -> None:
    objects, _ = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    by_name = {o.object_name: o for o in objects}
    assert by_name["Sample Date"].object_id == "OBJ_1"
    assert by_name["Sample Filter"].object_id == "FIL_1"
    assert by_name["Sample Date"].verification_status is EvidenceVerificationStatus.CONFIRMED


def test_select_and_where_expressions_are_extracted() -> None:
    _, expressions = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    by_id = {e.object_id: e for e in expressions}
    assert by_id["OBJ_1"].select_expression == "SAMPLE_TABLE.SAMPLE_DATE_COL"
    assert by_id["OBJ_1"].where_expression is None
    assert by_id["FIL_1"].where_expression == "SAMPLE_TABLE.SAMPLE_FLAG = 'Y'"
    assert by_id["FIL_1"].select_expression is None


def test_measure_projection_function_is_extracted() -> None:
    _, expressions = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    measure = next(e for e in expressions if e.object_id == "OBJ_3")
    assert measure.projection_function == "Sum"
    assert measure.select_expression == "SUM(SAMPLE_FACT.SAMPLE_AMT)"


def test_folder_path_is_preserved_on_objects() -> None:
    objects, _ = parse_business_layer_catalogs(SAMPLE_BLX_TEXT)
    dimension = next(o for o in objects if o.object_id == "OBJ_1")
    assert dimension.folder_path == "\\Sample Dimension Folder\\"
