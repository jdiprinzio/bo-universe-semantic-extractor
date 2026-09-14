"""Unit tests for the generic PDF text-parsing utilities."""

from __future__ import annotations

from bo_semantic_extractor.extractors.design_pdf import (
    extract_sequential_fields,
    join_block_lines,
    strip_page_markers,
)


def test_strip_page_markers_removes_standalone_page_footers() -> None:
    text = "Name Foo\n- 42 -\nCuid CLS_1\n"
    assert "- 42 -" not in strip_page_markers(text)
    assert "Name Foo" in strip_page_markers(text)


def test_join_block_lines_collapses_wrapped_text() -> None:
    block = "Description This is a long\ndescription that wraps\nacross lines.\nCuid OBJ_1"
    joined = join_block_lines(block)
    assert "\n" not in joined
    assert "Description This is a long description that wraps across lines. Cuid OBJ_1" == joined


def test_extract_sequential_fields_splits_in_order() -> None:
    text = "Name Foo Description Some text here Cuid CLS_1 Translation ID CLS_1 Path \\Root\\ State Active"
    fields = extract_sequential_fields(
        text, ["Name", "Description", "Cuid", "Translation ID", "Path", "State"]
    )
    assert fields["Name"] == "Foo"
    assert fields["Description"] == "Some text here"
    assert fields["Cuid"] == "CLS_1"
    assert fields["Path"] == "\\Root\\"
    assert fields["State"] == "Active"


def test_extract_sequential_fields_skips_missing_optional_labels() -> None:
    text = "Name Bar Cuid FIL_9 Translation ID FIL_9 Path \\Filters\\ State Active"
    fields = extract_sequential_fields(
        text, ["Name", "Description", "Cuid", "Translation ID", "Path", "State"]
    )
    assert "Description" not in fields
    assert fields["Cuid"] == "FIL_9"


def test_extract_sequential_fields_does_not_confuse_embedded_select_references() -> None:
    """An `@Select(...)` reference inside the Select value must not truncate that value."""
    text = (
        "Name Amt Cuid OBJ_9 Translation ID OBJ_9 Path \\Measures\\ State Active "
        "Data Type Numeric Projection Function Sum High Precision False SQL Definition "
        "Select SUM(Case When @Select(Date Dimension\\Year) = 1 Then TBL.COL Else 0 End) "
        "Advanced Minimum Object Level Security Public Data Sensitivity Category "
        "Uncategorized data Can be used in Results"
    )
    labels = [
        "Name", "Description", "Cuid", "Translation ID", "Path", "State", "Data Type",
        "Projection Function", "High Precision", "SQL Definition", "Select", "Advanced",
        "Minimum Object Level Security", "Data Sensitivity Category", "Can be used in",
    ]
    fields = extract_sequential_fields(text, labels)
    assert "@Select(Date Dimension" in fields["Select"]
    assert fields["Select"].endswith("Else 0 End)")
