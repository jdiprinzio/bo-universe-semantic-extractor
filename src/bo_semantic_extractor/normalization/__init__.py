"""Normalization schemas and conversion helpers.

`schemas.py` generates JSON Schema files from the typed Pydantic models so
`config/catalog_schema.json` and `normalization/schemas/*.schema.json` never drift from
`bo_semantic_extractor.models`. Run `python -m bo_semantic_extractor.normalization.schemas`
to regenerate them after changing a model.
"""

from __future__ import annotations
