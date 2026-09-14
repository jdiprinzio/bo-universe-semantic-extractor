"""BusinessObjects client interfaces (read-only).

`SemanticLayerClient` is the transport-agnostic Protocol; `RestSemanticLayerClient` is the
REST implementation. No SAP endpoint paths are hard-coded until confirmed (see rest_client.py).
"""

from __future__ import annotations

from bo_semantic_extractor.bo_client.base import SemanticLayerClient
from bo_semantic_extractor.bo_client.errors import (
    AmbiguousMatchError,
    ApiContractError,
    AuthenticationError,
    AuthorizationError,
    BoClientError,
    ConfigError,
    NotFoundError,
    PaginationError,
    RateLimitedError,
    SdkUnavailableError,
)
from bo_semantic_extractor.bo_client.rest_client import RestSemanticLayerClient

__all__ = [
    "AmbiguousMatchError",
    "ApiContractError",
    "AuthenticationError",
    "AuthorizationError",
    "BoClientError",
    "ConfigError",
    "NotFoundError",
    "PaginationError",
    "RateLimitedError",
    "RestSemanticLayerClient",
    "SdkUnavailableError",
    "SemanticLayerClient",
]
