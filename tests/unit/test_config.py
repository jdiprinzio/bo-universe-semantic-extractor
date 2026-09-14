"""Unit tests for configuration loading, including fail-closed behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bo_semantic_extractor.bo_client.errors import ConfigError
from bo_semantic_extractor.config import (
    load_app_config,
    load_environment_config,
    load_extraction_profile,
)

VALID_PROFILE: dict[str, object] = {
    "profile_name": "test",
    "universe": {"cuid": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
}

VALID_ENV = {
    "BO_BASE_URL": "https://bo.example.invalid",
    "BO_AUTH_TYPE": "secEnterprise",
    "BO_USERNAME": "sample-user",
    "BO_PASSWORD": "sample-password",
}


def _write_profile(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_extraction_profile_requires_universe_selector(tmp_path: Path) -> None:
    data: dict[str, object] = {"profile_name": "test", "universe": {}}
    path = _write_profile(tmp_path, data)
    with pytest.raises(ConfigError):
        load_extraction_profile(path)


def test_load_extraction_profile_accepts_valid_profile(tmp_path: Path) -> None:
    path = _write_profile(tmp_path, VALID_PROFILE)
    profile = load_extraction_profile(path)
    assert profile.universe.cuid == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    assert profile.extraction.fail_on_unknown_object_type is True


def test_load_extraction_profile_missing_file_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_extraction_profile(tmp_path / "does_not_exist.yaml")


def test_load_extraction_profile_rejects_non_read_only(tmp_path: Path) -> None:
    data: dict[str, object] = dict(VALID_PROFILE)
    data["security"] = {"read_only": False}
    path = _write_profile(tmp_path, data)
    with pytest.raises(ConfigError):
        load_extraction_profile(path)


def test_load_environment_config_requires_all_required_vars() -> None:
    with pytest.raises(ConfigError):
        load_environment_config({"BO_BASE_URL": "https://bo.example.invalid"})


def test_load_environment_config_succeeds_with_required_vars() -> None:
    config = load_environment_config(VALID_ENV)
    assert config.base_url == VALID_ENV["BO_BASE_URL"]
    assert config.password.get_secret_value() == "sample-password"


def test_load_app_config_combines_profile_and_environment(tmp_path: Path) -> None:
    path = _write_profile(tmp_path, VALID_PROFILE)
    config = load_app_config(path, VALID_ENV)
    assert config.profile.profile_name == "test"
    assert config.environment.username == "sample-user"
