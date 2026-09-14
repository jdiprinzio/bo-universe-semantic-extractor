"""PDF text extraction and generic labeled-field parsing for BLX/DFX design reports.

These reports (Apache FOP-generated IDT "print" exports) are **rendered derivatives** of the
real `.blx`/`.dfx` resources, not the resources themselves — see
`docs/dm_invoice_data_mart_extraction_roadmap.md` §1.1/§2.1. Graphical elements (icons for join
type, cardinality, alias/standard table distinction) are not recoverable as text and must never
be guessed from this input.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

_PAGE_MARKER_PATTERN = re.compile(r"^-\s*\d+\s*-$")


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF, page by page, joined with newlines."""
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def strip_page_markers(text: str) -> str:
    """Remove standalone page-number footer lines (e.g. `- 567 -`) from extracted PDF text."""
    lines = [line for line in text.splitlines() if not _PAGE_MARKER_PATTERN.match(line.strip())]
    return "\n".join(lines)


def join_block_lines(block_text: str) -> str:
    """Collapse a multi-line block into a single space-joined string for field extraction."""
    lines = [line.strip() for line in strip_page_markers(block_text).splitlines()]
    return " ".join(line for line in lines if line)


def extract_sequential_fields(text: str, labels: list[str]) -> dict[str, str]:
    """Split `text` into label -> value using an expected, ordered (but optional) label list.

    Each label is searched for starting only from the end of the previously found label, so
    labels appearing earlier in `labels` are never re-matched inside a later field's value
    (this avoids false matches from, e.g., an `@Select(...)` reference embedded inside a
    `Select` expression's own value). Labels not found are simply omitted from the result.
    """
    positions: list[tuple[str, int, int]] = []
    cursor = 0
    for label in labels:
        match = re.search(re.escape(label), text[cursor:])
        if match is None:
            continue
        start = cursor + match.start()
        end = cursor + match.end()
        positions.append((label, start, end))
        cursor = end

    result: dict[str, str] = {}
    for index, (label, _start, end) in enumerate(positions):
        next_start = positions[index + 1][1] if index + 1 < len(positions) else len(text)
        result[label] = text[end:next_start].strip()
    return result
