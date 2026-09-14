"""Unit tests for the Data Foundation (.dfx) PDF parser, using synthetic report-shaped text."""

from __future__ import annotations

from bo_semantic_extractor.models.common import EvidenceVerificationStatus
from bo_semantic_extractor.normalization.data_foundation_parser import (
    parse_data_foundation_joins,
    parse_data_foundation_tables,
)

SAMPLE_DFX_TEXT = """
Tables (4)
Table: SAMPLE_FACT
Table: SAMPLE_DIM
Derived Table: SAMPLE_DERIVED (SAMPLE_DIM)
Views (1)
View: SampleView
Joins (2)
JoinSAMPLE_DIM.KEY=SAMPLE_FACT.KEY
JoinSAMPLE_FACT.CUR_KEY=SAMPLE_CUR.CUR_KEY and SAMPLE_CUR.ACTIVE_IND = 'Y'
"""


def test_parses_standard_and_derived_tables_and_views() -> None:
    tables = parse_data_foundation_tables(SAMPLE_DFX_TEXT)
    names_by_type = {t.table_name: t.table_type for t in tables}
    assert names_by_type["SAMPLE_FACT"] == "UNKNOWN"
    assert names_by_type["SAMPLE_DIM"] == "UNKNOWN"
    assert names_by_type["SAMPLE_DERIVED (SAMPLE_DIM)"] == "derived"
    assert names_by_type["SampleView"] == "view"


def test_all_tables_are_confirmed_by_existence() -> None:
    tables = parse_data_foundation_tables(SAMPLE_DFX_TEXT)
    assert all(t.verification_status is EvidenceVerificationStatus.CONFIRMED for t in tables)


def test_parses_joins_in_document_order_with_sequential_ids() -> None:
    joins = parse_data_foundation_joins(SAMPLE_DFX_TEXT)
    assert [j.join_id for j in joins] == ["1", "2"]
    assert joins[0].left_object == "SAMPLE_DIM"
    assert joins[0].right_object == "SAMPLE_FACT"


def test_join_type_and_cardinality_are_always_unknown() -> None:
    joins = parse_data_foundation_joins(SAMPLE_DFX_TEXT)
    assert all(j.join_type == "UNKNOWN" for j in joins)
    assert all(j.cardinality == "UNKNOWN" for j in joins)


def test_compound_join_expression_is_preserved_verbatim() -> None:
    joins = parse_data_foundation_joins(SAMPLE_DFX_TEXT)
    compound = joins[1]
    assert compound.join_expression == "SAMPLE_FACT.CUR_KEY=SAMPLE_CUR.CUR_KEY and SAMPLE_CUR.ACTIVE_IND = 'Y'"
    assert compound.left_object == "SAMPLE_FACT"
    assert compound.right_object == "SAMPLE_CUR"


def test_unparseable_join_endpoints_are_marked_unresolved() -> None:
    text = "Joins (1)\nJoinSOME_TABLE=OTHER_TABLE_NO_COLUMNS\n"
    joins = parse_data_foundation_joins(text)
    assert joins[0].left_object == "UNKNOWN"
    assert joins[0].right_object == "UNKNOWN"
    assert joins[0].verification_status is EvidenceVerificationStatus.PARSED_UNVERIFIED
