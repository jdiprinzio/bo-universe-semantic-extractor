"""REST implementation of `SemanticLayerClient`.

Endpoint paths for the SAP BI Semantic Layer REST API are intentionally not hard-coded here:
none have yet been confirmed against official SAP documentation or supplied API specifications
for this environment. Each method raises `SdkUnavailableError` describing the exact
configuration/documentation prerequisite instead of guessing a URL, per the
bo-universe-semantic-extractor skill's "do not fabricate endpoint paths" rule.

Once confirmed endpoint paths are available (e.g. supplied via `config/extraction_profiles/*.yaml`
or official API documentation), fill in `_ENDPOINTS` and the corresponding request logic, then
replace the matching contract test in `tests/contract/` with a real assertion against sanitized
fixtures.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Self, TypeVar

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from bo_semantic_extractor.bo_client.base import SemanticLayerClient
from bo_semantic_extractor.bo_client.errors import (
    ConfigError,
    RateLimitedError,
    SdkUnavailableError,
)
from bo_semantic_extractor.models import RawArtifact, UniverseSummary

REQUIRED_ENV_VARS = ("BO_BASE_URL", "BO_AUTH_TYPE", "BO_USERNAME", "BO_PASSWORD")

_RETRYABLE_TRANSPORT_ERRORS = (httpx.ConnectTimeout, httpx.ReadTimeout, RateLimitedError)

_F = TypeVar("_F", bound=Callable[..., Any])


def _bounded_retry() -> Callable[[_F], _F]:
    """Bounded retry for transient transport errors only; never retries auth failures."""
    return retry(
        retry=retry_if_exception_type(_RETRYABLE_TRANSPORT_ERRORS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )


class RestSemanticLayerClient(SemanticLayerClient):
    """SAP BI Semantic Layer REST API client (read-only).

    Endpoint paths must be confirmed and configured before use; see module docstring.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        missing = [name for name in REQUIRED_ENV_VARS if not (base_url if name == "BO_BASE_URL" else os.environ.get(name))]
        if missing:
            raise ConfigError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Set these as environment variables (see .env.example)."
            )
        self._base_url = base_url or os.environ["BO_BASE_URL"]
        self._timeout = timeout
        self._client: httpx.Client | None = None

    def __enter__(self) -> Self:
        self._client = httpx.Client(base_url=self._base_url, timeout=self._timeout)
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @_bounded_retry()
    def list_universes(self) -> list[UniverseSummary]:
        raise SdkUnavailableError(
            "list_universes: no confirmed SAP BI Semantic Layer REST endpoint is configured. "
            "Supply the endpoint path once confirmed from official SAP documentation."
        )

    @_bounded_retry()
    def get_universe(self, universe_cuid: str) -> RawArtifact:
        raise SdkUnavailableError(
            "get_universe: no confirmed SAP BI Semantic Layer REST endpoint is configured. "
            "Supply the endpoint path once confirmed from official SAP documentation."
        )

    @_bounded_retry()
    def list_universe_objects(self, universe_cuid: str) -> list[RawArtifact]:
        raise SdkUnavailableError(
            "list_universe_objects: no confirmed SAP BI Semantic Layer REST endpoint is configured. "
            "Supply the endpoint path once confirmed from official SAP documentation."
        )

    @_bounded_retry()
    def list_dependent_documents(self, universe_cuid: str) -> list[RawArtifact]:
        raise SdkUnavailableError(
            "list_dependent_documents: no confirmed SAP Web Intelligence REST endpoint is "
            "configured. Supply the endpoint path once confirmed from official SAP documentation."
        )

    @_bounded_retry()
    def get_document_metadata(self, document_cuid: str) -> RawArtifact:
        raise SdkUnavailableError(
            "get_document_metadata: no confirmed SAP Web Intelligence REST endpoint is "
            "configured. Supply the endpoint path once confirmed from official SAP documentation."
        )
