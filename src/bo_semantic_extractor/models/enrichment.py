"""AI-proposed semantic enrichment, always kept separate from extracted facts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bo_semantic_extractor.models.common import ReviewStatus


class SemanticEnrichment(BaseModel):
    """A candidate business-friendly annotation for a `UniverseObject`.

    Never authoritative: `review_status` defaults to `AI_PROPOSED` and must only be
    changed by an explicit human review action, never by automated code.
    """

    canonical_term: str
    synonyms: list[str] = Field(default_factory=list)
    proposed_plain_language_definition: str | None = None
    proposed_compatible_dimensions: list[str] = Field(default_factory=list)
    proposed_required_filters: list[str] = Field(default_factory=list)
    proposed_question_examples: list[str] = Field(default_factory=list)
    generated_by_model: str
    generated_at_utc: datetime
    review_status: ReviewStatus = ReviewStatus.AI_PROPOSED
    reviewed_by: str | None = None
    reviewed_at_utc: datetime | None = None
