"""Configuration loading: extraction profile YAML + environment secrets.

Fails closed: raises `ConfigError` immediately when required settings are missing or invalid
rather than proceeding with partial configuration. Secrets always come from environment
variables (see `.env.example`); the YAML extraction profile carries only non-secret settings.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, SecretStr, ValidationError, model_validator

from bo_semantic_extractor.bo_client.errors import ConfigError

REQUIRED_ENV_VARS = ("BO_BASE_URL", "BO_AUTH_TYPE", "BO_USERNAME", "BO_PASSWORD")


class UniverseSelector(BaseModel):
    """Identifies the single target universe. CUID is preferred when both are present."""

    cuid: str | None = None
    exact_name: str | None = None
    expected_type: str = "UNX"

    @model_validator(mode="after")
    def _require_one_selector(self) -> UniverseSelector:
        if not self.cuid and not self.exact_name:
            raise ValueError("universe.cuid or universe.exact_name is required")
        return self


class RepositorySettings(BaseModel):
    folder_path: str | None = None


class ExtractionSettings(BaseModel):
    include_webi_dependencies: bool = True
    include_usage: bool = False
    include_hana_lineage: bool = False
    preserve_raw_responses: bool = True
    fail_on_unknown_object_type: bool = True
    max_documents: int = 500


class OutputSettings(BaseModel):
    root: str = "output"
    formats: list[str] = Field(default_factory=lambda: ["json", "csv", "markdown"])


class SecuritySettings(BaseModel):
    read_only: bool = True
    redact_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "Cookie", "Set-Cookie"]
    )

    @model_validator(mode="after")
    def _require_read_only(self) -> SecuritySettings:
        if not self.read_only:
            raise ValueError("security.read_only must be true; this pipeline is read-only.")
        return self


class ExtractionProfile(BaseModel):
    """Non-secret extraction settings, loaded from a YAML file such as `config/extraction_profiles/dev.yaml`."""

    profile_name: str
    universe: UniverseSelector
    repository: RepositorySettings = Field(default_factory=RepositorySettings)
    extraction: ExtractionSettings = Field(default_factory=ExtractionSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


class BoEnvironmentConfig(BaseModel):
    """Secrets and connection settings loaded only from environment variables."""

    base_url: str
    auth_type: str
    username: str
    password: SecretStr
    client_id: str | None = None
    client_secret: SecretStr | None = None
    hana_address: str | None = None
    hana_port: str | None = None
    hana_user: str | None = None
    hana_password: SecretStr | None = None
    log_level: str = "INFO"


@dataclass(frozen=True)
class AppConfig:
    profile: ExtractionProfile
    environment: BoEnvironmentConfig


def load_extraction_profile(path: Path) -> ExtractionProfile:
    """Load and validate an extraction profile YAML file. Fails closed on any problem."""
    if not path.exists():
        raise ConfigError(f"Extraction profile not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Extraction profile is not valid YAML: {path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"Extraction profile must be a YAML mapping: {path}")
    try:
        return ExtractionProfile.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Extraction profile failed validation ({path}): {exc}") from exc


def load_environment_config(env: Mapping[str, str] | None = None) -> BoEnvironmentConfig:
    """Load required/optional BO and HANA settings from environment variables. Fails closed."""
    source = env if env is not None else os.environ
    missing = [name for name in REQUIRED_ENV_VARS if not source.get(name)]
    if missing:
        raise ConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set these locally in a .env file (see .env.example) or your environment."
        )
    client_secret = source.get("BO_CLIENT_SECRET")
    hana_password = source.get("HANA_PASSWORD")
    return BoEnvironmentConfig(
        base_url=source["BO_BASE_URL"],
        auth_type=source["BO_AUTH_TYPE"],
        username=source["BO_USERNAME"],
        password=SecretStr(source["BO_PASSWORD"]),
        client_id=source.get("BO_CLIENT_ID") or None,
        client_secret=SecretStr(client_secret) if client_secret else None,
        hana_address=source.get("HANA_ADDRESS") or None,
        hana_port=source.get("HANA_PORT") or None,
        hana_user=source.get("HANA_USER") or None,
        hana_password=SecretStr(hana_password) if hana_password else None,
        log_level=source.get("BO_LOG_LEVEL", "INFO"),
    )


def load_app_config(profile_path: Path, env: Mapping[str, str] | None = None) -> AppConfig:
    """Load and combine the extraction profile and environment configuration."""
    return AppConfig(
        profile=load_extraction_profile(profile_path),
        environment=load_environment_config(env),
    )
