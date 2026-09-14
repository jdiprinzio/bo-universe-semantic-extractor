"""Contract tests for the BO REST client against sanitized fixtures.

These tests validate that (a) sanitized sample payloads conform to the `RawArtifact`
envelope, and (b) `RestSemanticLayerClient` fails closed with `SdkUnavailableError` rather
than guessing an unconfirmed SAP endpoint path. Once real endpoint paths are confirmed and
configured, replace the `test_*_requires_configured_endpoint` assertions with real
request/response contract checks against sanitized fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bo_semantic_extractor.bo_client.errors import ConfigError, SdkUnavailableError
from bo_semantic_extractor.bo_client.rest_client import RestSemanticLayerClient
from bo_semantic_extractor.models import RawArtifact

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bo_rest"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture_name",
    [
        "universe_detail.sample.json",
        "universe_objects.sample.json",
        "webi_documents.sample.json",
        "webi_document_metadata.sample.json",
        "auth_failure.sample.json",
    ],
)
def test_fixture_conforms_to_raw_artifact_envelope(fixture_name: str) -> None:
    """Every sanitized fixture must satisfy the RawArtifact evidence contract."""
    RawArtifact.model_validate(_load_fixture(fixture_name))


def test_rest_client_requires_base_url_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BO_BASE_URL", raising=False)
    monkeypatch.delenv("BO_USERNAME", raising=False)
    monkeypatch.delenv("BO_PASSWORD", raising=False)
    monkeypatch.setenv("BO_AUTH_TYPE", "secEnterprise")
    with pytest.raises(ConfigError):
        RestSemanticLayerClient()


def test_get_universe_requires_configured_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Documents that no SAP endpoint path is fabricated: the client fails closed instead."""
    monkeypatch.setenv("BO_AUTH_TYPE", "secEnterprise")
    monkeypatch.setenv("BO_USERNAME", "sample-user")
    monkeypatch.setenv("BO_PASSWORD", "sample-password")
    client = RestSemanticLayerClient(base_url="https://bo.example.invalid")
    with pytest.raises(SdkUnavailableError):
        client.get_universe("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
