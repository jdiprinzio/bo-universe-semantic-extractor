"""Normalized models for Web Intelligence documents and their dependencies."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WebIDocument(BaseModel):
    """A Web Intelligence document that depends on the extracted universe(s)."""

    document_cuid: str
    document_name: str
    repository_path: str
    universe_cuids: list[str] = Field(default_factory=list)
    last_modified_at: datetime | None = None
    extraction_source: str


class DataProvider(BaseModel):
    """A single query/data-provider within a Web Intelligence document."""

    document_cuid: str
    data_provider_id: str
    data_provider_name: str
    universe_cuid: str
    result_object_ids: list[str] = Field(default_factory=list)
    query_filters: list[str] = Field(default_factory=list)
    prompts: list[str] = Field(default_factory=list)
    query_properties: dict[str, str] = Field(default_factory=dict)


class ReportVariable(BaseModel):
    """A report-local variable, including formula and dependency references."""

    document_cuid: str
    variable_id: str
    variable_name: str
    qualification: str | None = None
    formula: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    extraction_source: str
