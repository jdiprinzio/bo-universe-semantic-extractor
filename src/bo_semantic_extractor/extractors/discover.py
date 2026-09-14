"""DISCOVER stage: resolve exactly one target universe by CUID or exact name."""

from __future__ import annotations

from bo_semantic_extractor.bo_client.base import SemanticLayerClient
from bo_semantic_extractor.bo_client.errors import AmbiguousMatchError, NotFoundError
from bo_semantic_extractor.config import UniverseSelector
from bo_semantic_extractor.models import UniverseSummary


def discover_universe(
    client: SemanticLayerClient, selector: UniverseSelector
) -> UniverseSummary:
    """Resolve the target universe. Prefers CUID; fails on multiple exact-name matches."""
    universes = client.list_universes()
    if selector.cuid:
        for universe in universes:
            if universe.universe_cuid == selector.cuid:
                return universe
        raise NotFoundError(f"No universe found with CUID {selector.cuid!r}.")

    matches = [u for u in universes if u.universe_name == selector.exact_name]
    if not matches:
        raise NotFoundError(f"No universe found with name {selector.exact_name!r}.")
    if len(matches) > 1:
        raise AmbiguousMatchError(
            f"Multiple universes named {selector.exact_name!r} found; use universe.cuid instead."
        )
    return matches[0]
